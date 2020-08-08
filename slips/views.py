import json
from datetime import datetime
from io import BytesIO

from client.models import client
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User as user
from django.db import transaction
from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from items.models import items
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas
from users.models import Employee
from django.http import HttpResponse

from .models import slip, slip_job


# Create your views here.
@login_required
def slips_add(request):
    item = list(items.objects.all().order_by('item_name'))
    clients = list(client.objects.all().order_by('client_name'))
    dt = datetime.now().strftime("%Y-%m-%d")
    return render(request, "slips_add.html", {"items": item, "clients": clients, 'datetime': dt})


@login_required
def slips_modify(request):
    item = list(items.objects.all().order_by('item_name'))
    clients = list(client.objects.all().order_by('client_name'))
    dt = datetime.now().strftime("%Y-%m-%d")
    slips = slip.objects.all()
    return render(request, "slips_modify.html", {"items": item, "clients": clients, 'datetime': dt, "slips": slips})


@login_required
def slips_delete(request):
    slips = slip.objects.filter(completed=False)
    return render(request, "slips_delete.html", {"slips": slips})


@login_required
def get_slip_jobs(request):
    data = json.loads(request.body)
    payload = {}
    for i in range(len(data)):
        payload[list(data[i].items())[0][0]] = list(data[i].items())[0][1]
    slip_job_objs = slip_job.objects.filter(slip_no=payload['slip_no'])
    slip_obj = get_object_or_404(slip, pk=payload['slip_no'])
    slip_obj_json = model_to_dict(slip_obj)
    dt = slip_obj_json["date"].strftime("%Y-%m-%d")
    slip_obj_json["date"] = dt
    response_json = {"slip_jobs": [], "slip": slip_obj_json}
    for i in range(len(slip_job_objs)):
        response_json["slip_jobs"].append(model_to_dict(slip_job_objs[i]))
    return JsonResponse(response_json)

@login_required
def print_slip_jobs(request):
    data = json.loads(request.body)
    payload = {}
    for i in range(len(data)):
        payload[list(data[i].items())[0][0]] = list(data[i].items())[0][1]
    pdf = slip_pdf(payload['slip_no'])
    http = HttpResponse(pdf, content_type='application/pdf')
    http['Content-Disposition'] = 'inline; filename="challan.pdf"'
    return http

@login_required
def update_status(request):
    request_post = dict(request.POST)
    jc_list = request_post['job_completed']
    jc_list_parsed = []
    offset = 0
    billed = True if 'True' in request_post['billed'] else False
    slip_obj = slip.objects.filter(slip_no=request_post['slip_no'][0])[0]
    if slip_obj.billed != billed:
        check_user = Employee.objects.get(user=user.objects.get(username=request.user))
        if check_user.role != 'Admin':
            s_objs = slip.objects.filter(completed=False)
            for s_obj in s_objs:
                s_job_objs = slip_job.objects.filter(completed=False, slip_no=s_obj.slip_no)
                s_obj.jobs_completed = "{0} jobs remaining".format(len(s_job_objs))
                if s_obj.jobs_completed == 0:
                    s_obj.jobs_completed = "Waiting to be delivered"
            return render(request, "slips_dashboard.html",
                          {"slip_objs": s_objs,
                           'error_message': "You dont have permission to check mark billed."})
    for i in range(len(jc_list)):
        if jc_list[i] == 'True':
            jc_list_parsed[i - 1 - offset] = True
            offset += 1
        else:
            jc_list_parsed.append(False)
    job_id_list = request_post['job_id']
    for i in range(len(job_id_list)):
        if job_id_list[i] != '':
            slip_job_obj = slip_job.objects.filter(job_id=job_id_list[i]).filter(slip_no=request_post['slip_no'][0])[0]
            slip_job_obj.completed = jc_list_parsed[i]
            slip_job_obj.save()    
    if billed:
        slip_obj.billed = True
        slip_obj.save()
    else:
        slip_obj.billed = False
        slip_obj.save()
    if request.POST["save_delivered"] == 'delivered':
        slip_obj.completed = True
        slip_obj.save()
    slip_objs = slip.objects.filter(completed=False)
    for slip_obj in slip_objs:
        slip_job_objs = slip_job.objects.filter(completed=False, slip_no=slip_obj.slip_no)
        slip_obj.jobs_completed = "{0} jobs remaining".format(len(slip_job_objs))
        if slip_obj.jobs_completed == 0:
            slip_obj.jobs_completed = "Waiting to be delivered"
    return render(request, "slips_dashboard.html", {"slip_objs": slip_objs, "success_message": "Slip updated successfully"})


@login_required
def submit_slip(request):
    item = list(items.objects.all().order_by('item_name'))
    clients = list(client.objects.all().order_by('client_name'))
    dt = datetime.now().strftime("%Y-%m-%d")
    request_post = dict(request.POST)
    fb_list = request_post['fb']
    fb_list_parsed = []
    offset = 0
    for i in range(len(fb_list)):
        if fb_list[i] == 'True':
            fb_list_parsed[i - 1 - offset] = True
            offset += 1
        else:
            fb_list_parsed.append(False)
    for i in range(len(request_post['rate'])):
        if request_post['rate'][i] == '0':
            index = i
            break
    for i in range(index):
        if float(request_post['rate'][i]) <= 0 or float(request_post['quantity'][i]) <= 0:
            return render(request, "slips_add.html", {"items": item,
                                                      "clients": clients, 'datetime': dt,
                                                      'error_message': "Cannot have empty rate or quantity"})
    for i in range(index, len(request_post['rate'])):
        if request_post['rate'][i] != '0' or request_post['quantity'][i] != '0':
            return render(request, "slips_add.html", {"items": item,
                                                      "clients": clients, 'datetime': dt,
                                                      'error_message': "Cannot have empty rate or quantity"})
    with transaction.atomic():
        client_obj = get_object_or_404(client, pk=request_post['client_name'][0])
        slip_obj = slip(date=request_post['date'][0], client_name=client_obj,
                        amount=float(request_post['total_amount'][0]), completed=False, billed=False)
        slip_obj.save()
        for i in range(index):
            slip_obj = slip.objects.filter(slip_no=slip_obj.slip_no)[0]
            item_obj = get_object_or_404(items, pk=request_post['item_name'][i])
            slip_job_obj = slip_job(job_id=i, slip_no=slip_obj, job_name=request_post['job_name'][i],
                                    item=item_obj, quantity=int(request_post['quantity'][i]),
                                    rate=float(request_post['rate'][i]),
                                    amount=float(request_post['amount'][i]), fb=fb_list_parsed[i], completed=False)
            slip_job_obj.save()
        return render(request, "slips_add.html", {"items": item,
                                                  "clients": clients, 'datetime': dt,
                                                  'success_message': "Slip Created Successfully"})


@login_required
def submit_slip_modify(request):
    item = list(items.objects.all().order_by('item_name'))
    clients = list(client.objects.all().order_by('client_name'))
    dt = datetime.now().strftime("%Y-%m-%d")
    request_post = dict(request.POST)
    fb_list = request_post['fb']
    fb_list_parsed = []
    offset = 0
    slips = slip.objects.all()
    check_user = Employee.objects.get(user=user.objects.get(username=request.user))
    completed = True if 'True' in request_post['completed'] else False
    billed = True if 'True' in request_post['billed'] else False
    if check_user.role != 'Admin':
        return render(request, "slips_modify.html",
                      {"items": item, "clients": clients, 'datetime': dt, "slips": slips,
                       'error_message': "You dont have permission to modify anything."})
    for i in range(len(fb_list)):
        if fb_list[i] == 'True':
            fb_list_parsed[i - 1 - offset] = True
            offset += 1
        else:
            fb_list_parsed.append(False)
    for i in range(len(request_post['rate'])):
        if request_post['rate'][i] == '0':
            index = i
            break
    for i in range(index):
        if float(request_post['rate'][i]) <= 0 or float(request_post['quantity'][i]) <= 0 or request_post['job_name'][
            i] == '':
            return render(request, "slips_modify.html",
                          {"items": item, "clients": clients, 'datetime': dt, "slips": slips,
                           'error_message': "Cannot have empty rate or quantity or job_name"})
    for i in range(index, len(request_post['rate'])):
        if request_post['rate'][i] != '0' or request_post['quantity'][i] != '0' or request_post['job_name'][i] != '':
            return render(request, "slips_modify.html",
                          {"items": item, "clients": clients, 'datetime': dt, "slips": slips,
                           'error_message': "Cannot have empty rate or quantity or job_name"})
    with transaction.atomic():
        client_obj = get_object_or_404(client, pk=request_post['client_name'][0])
        slip_obj = slip.objects.filter(slip_no=request_post['slip_no'][0])[0]
        slip_obj.client_name = client_obj
        slip_obj.amount = request_post['total_amount'][0]
        slip_obj.completed = completed
        slip_obj.billed = billed
        slip_obj.save()
        slip_jobs_objs = slip_job.objects.filter(slip_no=slip_obj.slip_no)
        for slip_job_obj in slip_jobs_objs:
            slip_job_obj.delete()
        for i in range(index):
            item_obj = get_object_or_404(items, pk=request_post['item_name'][i])
            slip_obj = slip.objects.filter(slip_no=slip_obj.slip_no)[0]
            slip_job_obj = slip_job(job_id=i, slip_no=slip_obj, job_name=request_post['job_name'][i],
                                    item=item_obj, quantity=int(request_post['quantity'][i]),
                                    rate=float(request_post['rate'][i]),
                                    amount=float(request_post['amount'][i]), fb=fb_list_parsed[i], completed=False)
            slip_job_obj.save()
        return render(request, "slips_modify.html",
                      {"items": item, "clients": clients, 'datetime': dt, "slips": slips,
                       'success_message': "Slip Modified Successfully"})


@login_required
def submit_slip_delete(request):
    request_post = dict(request.POST)
    slips = slip.objects.filter(completed=False)
    check_user = Employee.objects.get(user=user.objects.get(username=request.user))
    if check_user.role != 'Admin':
        return render(request, "slips_delete.html",
                      {"slips": slips,
                       'error_message': "You dont have permission to delete anything."})
    with transaction.atomic():
        slip_obj = slip.objects.filter(slip_no=request_post['slip_no'][0])[0]
        slip_jobs_objs = slip_job.objects.filter(slip_no=slip_obj.slip_no)
        for slip_job_obj in slip_jobs_objs:
            slip_job_obj.delete()
        slip_obj.delete()
        return render(request, "slips_delete.html",
                      {"slips": slips,
                       'success_message': "Slip deleted successfully"})


@login_required
def slip_dashboard_page(request):
    slip_objs = slip.objects.filter(completed=False)
    for slip_obj in slip_objs:
        slip_job_objs = slip_job.objects.filter(completed=False, slip_no=slip_obj.slip_no)
        slip_obj.jobs_completed = "{0} jobs remaining".format(len(slip_job_objs))
        if slip_obj.jobs_completed == 0:
            slip_obj.jobs_completed = "Waiting to be delivered"
    return render(request, "slips_dashboard.html", {"slip_objs": slip_objs})


def slip_pdf(slip_no):
    slip_obj = get_object_or_404(slip, pk=slip_no)
    slip_job_objs = slip_job.objects.filter(slip_no=slip_no)
    slip_job_objs = sorted(slip_job_objs, key=lambda instance: instance.job_id)
    buffer = BytesIO()
    cnvs = canvas.Canvas(buffer, pagesize=A5)
    cnvs.setLineWidth(.6)
    cnvs.setFont('Helvetica', 12)
    cnvs.translate(mm, mm)
    cnvs.rect(5 * mm, 5 * mm, 136 * mm, 175 * mm, stroke=1, fill=0)
    cnvs.setFont('Helvetica-Bold', 14)
    cnvs.drawString((A5[0] - stringWidth('PK Scan Graphics', 'Helvetica-Bold', 14)) / 2, A5[1] - 40, 'PK Scan Graphics')
    cnvs.setFont('Helvetica', 12)
    cnvs.drawString(
        (A5[0] - stringWidth('4206, Hansa Puri Road, Budh Nagar, Tri Nagar, New Delhi-110035', 'Helvetica', 12)) / 2,
        A5[1] - 60, '4206, Hansa Puri Road, Budh Nagar, Tri Nagar, New Delhi-110035')
    cnvs.setFont('Helvetica-Bold', 14)
    cnvs.drawString((A5[0] - stringWidth('Job Booking Slip', 'Helvetica-Bold', 14)) / 2, A5[1] - 80, 'Job Booking Slip')
    cnvs.setFont('Helvetica', 10)
    cnvs.drawString(11 * mm, A5[1] - 100, 'Slip No.    ' + str(slip_obj.slip_no))
    cnvs.setFont('Helvetica-Bold', 12)
    cnvs.drawString(11 * mm, A5[1] - 115, 'Party    ' + str(slip_obj.client_name.client_name))
    cnvs.setFont('Helvetica', 10)
    cnvs.drawString(11 * mm, A5[1] - 130, 'Phone No.    ' + str(slip_obj.client_name.phone1))
    cnvs.drawString(90 * mm, A5[1] - 100, 'Date    ' + str(slip_obj.date.strftime('%d/%m/%Y')))
    cnvs.line(5 * mm, A5[1] - 133, 141 * mm, A5[1] - 133)
    cnvs.line(5 * mm, A5[1] - 153, 141 * mm, A5[1] - 153)
    cnvs.setFont('Helvetica-Bold', 10)
    cnvs.setFont('Helvetica', 10)
    cnvs.line(123 * mm, A5[1] - 450, 141 * mm, A5[1] - 450)
    cnvs.line(123 * mm, A5[1] - 449, 141 * mm, A5[1] - 449)
    cnvs.setFont('Helvetica', 10)
    cnvs.line(123 * mm, A5[1] - 450, 141 * mm, A5[1] - 450)
    cnvs.line(123 * mm, A5[1] - 449, 141 * mm, A5[1] - 449)
    cnvs.drawString(121 * mm - stringWidth('Total Balance', 'Helvetica', 10), A5[1] - 445, 'Total Balance')
    cnvs.drawString(140 * mm - stringWidth(str(slip_obj.amount), 'Helvetica', 10), A5[1] - 445,str(slip_obj.amount))
    cnvs.line(5 * mm, A5[1] - 433, 141 * mm, A5[1] - 433)
    cnvs.line(123 * mm, A5[1] - 133, 123 * mm, A5[1] - 450)
    cnvs.line(112 * mm, A5[1] - 133, 112 * mm, A5[1] - 433)
    cnvs.line(103 * mm, A5[1] - 133, 103 * mm, A5[1] - 433)
    cnvs.line(46 * mm, A5[1] - 133, 46 * mm, A5[1] - 433)
    cnvs.line(15 * mm, A5[1] - 133, 15 * mm, A5[1] - 433)
    cnvs.drawString(8 * mm, A5[1] - 146, 'No.')
    cnvs.drawString(20 * mm, A5[1] - 146, 'Job Name')
    cnvs.drawString(55 * mm, A5[1] - 146, 'Item Name')
    cnvs.drawString(104 * mm, A5[1] - 146, 'Qty.')
    cnvs.drawString(114 * mm, A5[1] - 146, 'Rate')
    cnvs.drawString(126 * mm, A5[1] - 146, 'Amount')
    cnvs.setFont('Helvetica', 9)
    first = 165
    for i in range(len(slip_job_objs)):
        cnvs.drawString(8 * mm, A5[1] - first - (13 * i), str(slip_job_objs[i].job_id + 1))
        cnvs.drawString(18 * mm, A5[1] - first - (13 * i), str(slip_job_objs[i].job_name))
        cnvs.drawString(48 * mm, A5[1] - first - (13 * i), slip_job_objs[i].item.item_name)
        cnvs.drawString(104 * mm, A5[1] - first - (13 * i), str(slip_job_objs[i].quantity))
        cnvs.drawString(114 * mm, A5[1] - first - (13 * i), str(round(slip_job_objs[i].rate, 2)))
        cnvs.drawString(126 * mm, A5[1] - first - (13 * i), str(round(slip_job_objs[i].amount, 2)))
    cnvs.showPage()
    cnvs.save()
    pdf = buffer.getvalue()

    buffer.close()
    return pdf
