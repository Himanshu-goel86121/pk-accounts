import json
# Create your views here.
from datetime import datetime
from email.mime.application import MIMEApplication
from io import BytesIO

from bill.models import bill
from client.models import client
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User as user
from django.core import serializers
from django.core.mail import EmailMessage
from django.db import transaction
from django.db.models import Max
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from fchallan.models import fchallan
from items.models import items
from logs.models import logs
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas
from users.models import Employee

from .models import pchallan, pjob


@login_required
def pchallan_add(request):
    item = list(items.objects.all().order_by('item_name'))
    clients = list(client.objects.all().order_by('client_name'))
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    dt = dt.split(" ")[0] + "T" + dt.split(" ")[1]
    return render(request, "pchallan_add.html", {"items": item, "clients": clients, 'datetime': dt})


@login_required
def pchallan_delete(request):
    pchallans = pchallan.objects.filter(deleted=False).filter(bill_no=None).order_by('challan_no')
    pchallans_json = serializers.serialize('json', pchallans)
    return render(request, "pchallan_delete.html", {"pchallans": list(pchallans), "pchallans_json": pchallans_json})


@login_required
def pchallan_modify(request):
    item = list(items.objects.all().order_by('item_name'))
    clients = list(client.objects.all().order_by('client_name'))
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    dt = dt.split(" ")[0] + "T" + dt.split(" ")[1]
    pchallans = list(pchallan.objects.order_by('challan_no'))
    return render(request, "pchallan_modify.html",
                  {"pchallans": pchallans, "items": item, "clients": clients, 'datetime': dt})


@login_required
def pchallan_modify_bill(request):
    item = list(items.objects.all().order_by('item_name'))
    clients = list(client.objects.all().order_by('client_name'))
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    dt = dt.split(" ")[0] + "T" + dt.split(" ")[1]
    pchallans = list(pchallan.objects.filter(deleted=False).filter(single_bill=True).order_by('challan_no'))
    return render(request, "pchallan_bill_modify.html",
                  {"pchallans": pchallans, "items": item, "clients": clients, 'datetime': dt})


@login_required
def pchallan_display(request):
    pchallans = list(pchallan.objects.filter(deleted=False).filter(bill_no=None).order_by('challan_no'))
    clients = list(client.objects.all().order_by('client_name'))
    return render(request, "pchallan_get.html", {"pchallans": pchallans, "clients": clients})


@login_required
def filter_date(request):
    pchallans = list(pchallan.objects.filter(deleted=False).filter(bill_no=None).filter(
        date__range=(request.POST['from'], request.POST['to'])))
    clients = list(client.objects.all().order_by('client_name'))
    return render(request, "pchallan_get.html", {"pchallans": pchallans, "clients": clients})


@login_required
def filter_client(request):
    pchallans = list(pchallan.objects.filter(deleted=False).filter(bill_no=None).filter(
        client_name=request.POST['client_name']).order_by('challan_no'))
    clients = list(client.objects.all().order_by('client_name'))
    return render(request, "pchallan_get.html", {"pchallans": pchallans, "clients": clients})


@login_required
def filter_challan_no(request):
    pchallans = list(pchallan.objects.filter(deleted=False).filter(bill_no=None).filter(
        challan_no=request.POST['challan_no']).order_by('challan_no'))
    clients = list(client.objects.all().order_by('client_name'))
    return render(request, "pchallan_get.html", {"pchallans": pchallans, "clients": clients})


@login_required
def pchallan_get(request):
    if 'button_1' in list(request.POST.keys()):
        item = list(items.objects.all().order_by('item_name'))
        clients = list(client.objects.all().order_by('client_name'))
        dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pchallans = list(pchallan.objects.order_by('challan_no'))
        pchallan_grp = get_object_or_404(pchallan, pk=request.POST['challan_no'])
        pjob_grp = pjob.objects.filter(challan_no=request.POST['challan_no'])
        for pjob_ in pjob_grp:
            pjob_.job_date = pjob_.job_date.strftime('%Y-%m-%d %H:%M:%S')
        pchallan_grp.date = pchallan_grp.date.strftime("%Y-%m-%d %H:%M:%S")
        pchallan_grp.date = pchallan_grp.date.split(" ")[0] + "T" + pchallan_grp.date.split(" ")[1]
        # datetime.strptime(pchallan_grp.date, '%b %d,%Y %H:%M:%S')
        dt = dt.split(" ")[0] + "T" + dt.split(" ")[1]
        return render(request, "pchallan_modify.html",
                      {"items": item, "pjob_grp": pjob_grp, "clients": clients, 'datetime': dt, 'pchallans': pchallans,
                       'pchallan_grp': pchallan_grp})
    elif 'button_2' in list(request.POST.keys()):
        pdf = pchallan_pdf(request.POST['challan_no'])
        http = HttpResponse(pdf, content_type='application/pdf')
        http['Content-Disposition'] = 'inline; filename="challan.pdf"'
        return http
    else:
        item = list(items.objects.all().order_by('item_name'))
        clients = list(client.objects.all().order_by('client_name'))
        dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pchallans = list(pchallan.objects.order_by('challan_no'))
        filtered_pchallans = pchallan.objects.filter(client_name=request.POST['client_name_filter']).order_by("-challan_no")[
                             :5]
        for filtered_pchallan in filtered_pchallans:
            filtered_pchallan.date = filtered_pchallan.date.strftime('%Y-%m-%d %H:%M:%S')
            filtered_pchallan.date = filtered_pchallan.date.split(" ")[0] + "T" + filtered_pchallan.date.split(" ")[1]
            pjob_objs = pjob.objects.filter(challan_no=filtered_pchallan.challan_no)[:2]
            pjob_names = ["", ""]
            for i in range(len(pjob_objs)):
                pjob_names[i] = pjob_objs[i].job_name
            filtered_pchallan.pjob1 = pjob_names[0]
            filtered_pchallan.pjob2 = pjob_names[1]
        dt = dt.split(" ")[0] + "T" + dt.split(" ")[1]
        return render(request, "pchallan_modify.html",
                      {"items": item, "clients": clients, 'datetime': dt, 'pchallans': pchallans,
                       "filtered_pchallans": filtered_pchallans})


@login_required
def pchallan_get_bill(request):
    if ('button_1' in list(request.POST.keys())):
        challan_no = \
            list(pchallan.objects.filter(deleted=False).filter(single_bill=True).filter(
                bill_no=request.POST['bill_no']))[
                0].challan_no
        item = list(items.objects.all().order_by('item_name'))
        clients = list(client.objects.all().order_by('client_name'))
        dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pchallans = list(pchallan.objects.filter(deleted=False).filter(single_bill=True).order_by('challan_no'))
        pchallan_grp = get_object_or_404(pchallan, pk=challan_no)
        pjob_grp = pjob.objects.all().filter(challan_no=challan_no)
        for pjob_ in pjob_grp:
            pjob_.job_date = pjob_.job_date.strftime('%Y-%m-%d %H:%M:%S')
        pchallan_grp.date = pchallan_grp.date.strftime("%Y-%m-%d %H:%M:%S")
        pchallan_grp.date = pchallan_grp.date.split(" ")[0] + "T" + pchallan_grp.date.split(" ")[1]
        # datetime.strptime(pchallan_grp.date, '%b %d,%Y %H:%M:%S')
        dt = dt.split(" ")[0] + "T" + dt.split(" ")[1]
        return render(request, "pchallan_bill_modify.html",
                      {"items": item, "pjob_grp": pjob_grp, "clients": clients, 'datetime': dt, 'pchallans': pchallans,
                       'pchallan_grp': pchallan_grp})
    elif ('button_2' in list(request.POST.keys())):
        pdf = bill_pdf(request.POST['bill_no'])
        http = HttpResponse(pdf, content_type='application/pdf')
        http['Content-Disposition'] = 'inline; filename="bill.pdf"'
        return http
    else:
        item = list(items.objects.all().order_by('item_name'))
        clients = list(client.objects.all().order_by('client_name'))
        dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pchallans = list(pchallan.objects.filter(deleted=False).filter(
            single_bill=True).order_by('challan_no'))
        filtered_pchallans = pchallan.objects.filter(client_name=request.POST['client_name_filter']).filter(
            deleted=False).filter(
            single_bill=True).order_by("-challan_no")[:5]
        for filtered_pchallan in filtered_pchallans:
            filtered_pchallan.date = filtered_pchallan.date.strftime('%Y-%m-%d %H:%M:%S')
            filtered_pchallan.date = filtered_pchallan.date.split(" ")[0] + "T" + filtered_pchallan.date.split(" ")[1]
            pjob_objs = pjob.objects.filter(challan_no=filtered_pchallan.challan_no)[:2]
            pjob_names = ["", ""]
            for i in range(len(pjob_objs)):
                pjob_names[i] = pjob_objs[i].job_name
            filtered_pchallan.pjob1 = pjob_names[0]
            filtered_pchallan.pjob2 = pjob_names[1]
            print(filtered_pchallan.pjob1, filtered_pchallan.pjob2)
        dt = dt.split(" ")[0] + "T" + dt.split(" ")[1]
        return render(request, "pchallan_bill_modify.html",
                      {"items": item, "clients": clients, 'datetime': dt, 'pchallans': pchallans,
                       "filtered_pchallans": filtered_pchallans})


@login_required
def add_pchallan(request):
    item = list(items.objects.all().order_by('item_name'))
    clients = list(client.objects.all().order_by('client_name'))
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    dt = dt.split(" ")[0] + "T" + dt.split(" ")[1]
    try:
        data = json.loads(request.body)
        dictt = {}
        for i in range(len(data)):
            dictt[list(data[i].items())[0][0]] = list(data[i].items())[0][1]
        table = []
        for i in range(len(dictt['table'])):
            row = {}
            for j in range(len(dictt['table'][i]['value'])):
                row['serial'] = dictt['table'][i]['key']
                row[list(dictt['table'][i]['value'][j].items())[0][0]] = list(dictt['table'][i]['value'][j].items())[0][
                    1]
            table.append(row)
        dictt['table'] = table
        print(dictt)
        with transaction.atomic():
            clientt = get_object_or_404(client, pk=dictt['client_name'])
            ch_no = pchallan.objects.all().aggregate(Max('challan_no'))
            if ch_no['challan_no__max']:
                max_challan = ch_no['challan_no__max']
            else:
                max_challan = 0
            challan = pchallan(challan_no=(max_challan + 1), date=dictt['date'], recieved=0,
                               payment_no=None, bill_no=None, single_bill=False, client_name=clientt,
                               gross_amount=dictt['gross_amount'], other_amount=dictt['other_amount'],
                               total_amount=dictt['total_amount'], gst=dictt['gst'], deleted=False)
            challan.save()
            try:
                print("challan no ", challan.challan_no)
            except:
                pass
            sum = 0
            for i in range(len(dictt['table'])):
                itemm = get_object_or_404(items, pk=dictt['table'][i]['item'])
                challan_no = get_object_or_404(pchallan, pk=challan.challan_no)
                job = pjob(job_id=dictt['table'][i]['serial'], slip_no=dictt['table'][i]['slip_no'],
                           gst=dictt['table'][i]['gst'], challan_no=challan_no, job_date=dictt['table'][i]['job_date'],
                           job_name=dictt['table'][i]['job_name'].strip(), item=itemm,
                           quantity=dictt['table'][i]['quantity'], unit=dictt['table'][i]['unit'],
                           rate=dictt['table'][i]['rate'],
                           amount=(float(dictt['table'][i]['rate']) * float(dictt['table'][i]['quantity'])))
                sum += float(job.gst) + job.amount
                job.save()
            if (abs(int(sum) - int(float(challan.total_amount))) > 2):
                raise Exception('The total amount is wrong please try again')
        pdf = pchallan_pdf(challan.challan_no)
        pdf_mime = MIMEApplication(pdf, _subtype='pdf')
        pdf_mime.add_header('content-disposition', 'attachment')
        email = EmailMessage(
            'Challan No.: {0}'.format(challan.challan_no),
            'Please find an attachment to the challan from pkscan graphics accounts',
            'pkscan.acc@gmail.com',
            [clientt.email],
            [],
            reply_to=[],
            headers={'Message-ID': 'foo'},
            attachments=[pdf_mime]
        )
        email.send()
        http = HttpResponse(pdf, content_type='application/pdf')
        http['Content-Disposition'] = 'inline; filename="challan.pdf"'
        l = logs(user_name=str(request.user),
                 message="Added a challan(Print) for " + str(dictt['client_name']) + " with challan no " + str(
                     challan.challan_no) + ".")
        l.save()
        return http
    except Exception as e:
        print(e)
        if (str(e) == 'The total amount is wrong please try again'):
            return render(request, 'pchallan_add.html', {"items": item, "clients": clients, 'datetime': dt,
                                                         'error_message': "The total amount is wrong please try again", })
        print(e.__class__.__name__)
        if (str(e.__class__.__name__) == 'DataError'):
            return render(request, 'pchallan_add.html', {"items": item, "clients": clients, 'datetime': dt,
                                                         'error_message': "Please provide the data correctly", })
        if (str(e.__class__.__name__) == 'ValidationError'):
            return render(request, 'pchallan_add.html', {"items": item, "clients": clients, 'datetime': dt,
                                                         'error_message': "Please provide the data correctly", })
        else:
            return render(request, 'pchallan_add.html',
                          {"items": item, "clients": clients, 'datetime': dt, 'error_message': "Some error occured", })


@login_required
def add_bill(request):
    item = list(items.objects.all().order_by('item_name'))
    clients = list(client.objects.all().order_by('client_name'))
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    dt = dt.split(" ")[0] + "T" + dt.split(" ")[1]
    try:
        data = json.loads(request.body)
        dictt = {}
        for i in range(len(data)):
            dictt[list(data[i].items())[0][0]] = list(data[i].items())[0][1]
        table = []
        for i in range(len(dictt['table'])):
            row = {}
            for j in range(len(dictt['table'][i]['value'])):
                row['serial'] = dictt['table'][i]['key']
                row[list(dictt['table'][i]['value'][j].items())[0][0]] = list(dictt['table'][i]['value'][j].items())[0][
                    1]
            table.append(row)
        dictt['table'] = table
        print(dictt)
        with transaction.atomic():
            clientt = get_object_or_404(client, pk=dictt['client_name'])
            bil_no = bill.objects.all().aggregate(Max('bill_no'))
            if bil_no['bill_no__max']:
                max_bill = bil_no['bill_no__max']
            else:
                max_bill = 0
            bil = bill(bill_no=(max_bill + 1), date=dictt['date'], client_name=clientt,
                       gross_amount=dictt['gross_amount'], other_amount=dictt['other_amount'],
                       total_amount=dictt['total_amount'], gst=dictt['gst'], recieved=0, deleted=False)
            bil.save()
            ch_no = pchallan.objects.all().aggregate(Max('challan_no'))
            if ch_no['challan_no__max']:
                max_challan = ch_no['challan_no__max']
            else:
                max_challan = 0
            challan = pchallan(challan_no=(max_challan + 1), date=dictt['date'], recieved=0,
                               payment_no=None, bill_no=bil, single_bill=True, client_name=clientt,
                               gross_amount=dictt['gross_amount'], other_amount=dictt['other_amount'],
                               total_amount=dictt['total_amount'], gst=dictt['gst'], deleted=False)
            challan.save()
            sum = 0
            for i in range(len(dictt['table'])):
                itemm = get_object_or_404(items, pk=dictt['table'][i]['item'])
                challan_no = get_object_or_404(pchallan, pk=challan.challan_no)
                job = pjob(job_id=dictt['table'][i]['serial'], slip_no=dictt['table'][i]['slip_no'],
                           gst=dictt['table'][i]['gst'], challan_no=challan_no, job_date=dictt['table'][i]['job_date'],
                           job_name=dictt['table'][i]['job_name'].strip(), item=itemm,
                           quantity=dictt['table'][i]['quantity'], unit=dictt['table'][i]['unit'],
                           rate=dictt['table'][i]['rate'],
                           amount=(float(dictt['table'][i]['rate']) * float(dictt['table'][i]['quantity'])))
                sum += float(job.gst) + job.amount
                job.save()
            if (abs(int(sum) - int(float(challan.total_amount))) > 2):
                raise Exception('The total amount is wrong please try again')
        print('It was successfully')
        pdf = bill_pdf(bil.bill_no, original=True)
        pdf_mime = MIMEApplication(pdf, _subtype='pdf')
        pdf_mime.add_header('content-disposition', 'attachment')
        email = EmailMessage(
            'Bill No.: {0}'.format(bil.bill_no),
            'Please find an attachment to the bill from pkscan graphics accounts',
            'pkscan.acc@gmail.com',
            [clientt.email],
            [],
            reply_to=[],
            headers={'Message-ID': 'foo'},
            attachments=[pdf_mime]
        )
        email.send()
        http = HttpResponse(pdf, content_type='application/pdf')
        http['Content-Disposition'] = 'inline; filename="challan.pdf"'
        l = logs(user_name=str(request.user),
                 message="Added a bill(Print) for " + str(dictt['client_name']) + " with bill no " + str(
                     bil.bill_no) + ".")
        l.save()
        return http
    except Exception as e:
        print(e)
        if (str(e) == 'The total amount is wrong please try again'):
            return render(request, 'pchallan_add.html', {"items": item, "clients": clients, 'datetime': dt,
                                                         'error_message': "The total amount is wrong please try again", })
        print(e.__class__.__name__)
        if (str(e.__class__.__name__) == 'DataError'):
            return render(request, 'pchallan_add.html', {"items": item, "clients": clients, 'datetime': dt,
                                                         'error_message': "Please provide the data correctly", })
        if (str(e.__class__.__name__) == 'ValidationError'):
            return render(request, 'pchallan_add.html', {"items": item, "clients": clients, 'datetime': dt,
                                                         'error_message': "Please provide the data correctly", })
        else:
            return render(request, 'pchallan_add.html',
                          {"items": item, "clients": clients, 'datetime': dt, 'error_message': "Some error occured", })


@login_required
def modify_pchallan(request):
    item = list(items.objects.all().order_by('item_name'))
    clients = list(client.objects.all().order_by('client_name'))
    pchallans = list(pchallan.objects.order_by('challan_no'))
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    dt = dt.split(" ")[0] + "T" + dt.split(" ")[1]
    check_user = Employee.objects.get(user=user.objects.get(username=request.user))
    if (check_user.role != 'Admin'):
        return render(request, 'pchallan_modify.html',
                      {"pchallans": pchallans, "items": item, "clients": clients, 'datetime': dt,
                       'error_message': "You dont have the permission to modify anything", })
    try:
        data = json.loads(request.body)
        dictt = {}
        for i in range(len(data)):
            dictt[list(data[i].items())[0][0]] = list(data[i].items())[0][1]
        table = []
        for i in range(len(dictt['table'])):
            row = {}
            for j in range(len(dictt['table'][i]['value'])):
                row['serial'] = dictt['table'][i]['key']
                row[list(dictt['table'][i]['value'][j].items())[0][0]] = list(dictt['table'][i]['value'][j].items())[0][
                    1]
            table.append(row)
        dictt['table'] = table
        with transaction.atomic():
            clientt = get_object_or_404(client, pk=dictt['client_name'])
            challan = get_object_or_404(pchallan, pk=dictt['challan_no'])
            if (challan.payment_no != None):
                return render(request, 'pchallan_bill_modify.html',
                              {"pchallans": pchallans, "items": item, "clients": clients, 'datetime': dt,
                               'error_message': "You can't modify a paid challan", })
            dictt['date'] = dictt['date'].replace('T', ' ')
            challan.date = datetime.strptime(dictt['date'], '%Y-%m-%d %H:%M:%S')
            challan.client_name = clientt
            challan.gross_amount = dictt['gross_amount']
            challan.other_amount = dictt['other_amount']
            challan.total_amount = dictt['total_amount']
            challan.gst = dictt['gst']
            challan.deleted = False
            challan.save()
            print(dictt['table'])
            try:
                print("challan no ", challan.challan_no)
            except:
                pass
            pjobs = pjob.objects.all().filter(challan_no=dictt['challan_no'])
            for pj in pjobs:
                pj.delete()
            sum = 0
            for i in range(len(dictt['table'])):
                itemm = get_object_or_404(items, pk=dictt['table'][i]['item'])
                challan_no = get_object_or_404(pchallan, pk=challan.challan_no)
                try:
                    job = pjob(job_id=dictt['table'][i]['serial'], slip_no=dictt['table'][i]['slip_no'],
                               gst=dictt['table'][i]['gst'], challan_no=challan_no, job_date=datetime.strptime(
                            dictt['table'][i]['job_date'].replace(',', '').replace('.', ''), '%b %d %Y %I:%M %p'),
                               job_name=dictt['table'][i]['job_name'].strip(), item=itemm,
                               quantity=dictt['table'][i]['quantity'], unit=dictt['table'][i]['unit'],
                               rate=dictt['table'][i]['rate'],
                               amount=(float(dictt['table'][i]['rate']) * float(dictt['table'][i]['quantity'])))
                except:
                    try:
                        job = pjob(job_id=dictt['table'][i]['serial'], slip_no=dictt['table'][i]['slip_no'],
                                   gst=dictt['table'][i]['gst'], challan_no=challan_no,
                                   job_date=datetime.strptime(dictt['table'][i]['job_date'].replace('T', ' '),
                                                              '%Y-%m-%d %H:%M:%S'),
                                   job_name=dictt['table'][i]['job_name'].strip(), item=itemm,
                                   quantity=dictt['table'][i]['quantity'], unit=dictt['table'][i]['unit'],
                                   rate=dictt['table'][i]['rate'],
                                   amount=(float(dictt['table'][i]['rate']) * float(dictt['table'][i]['quantity'])))
                    except:
                        try:
                            job = pjob(job_id=dictt['table'][i]['serial'], slip_no=dictt['table'][i]['slip_no'],
                                       gst=dictt['table'][i]['gst'], challan_no=challan_no, job_date=datetime.strptime(
                                    dictt['table'][i]['job_date'].replace(',', '').replace('.', ''),
                                    '%B %d %Y %I:%M %p'), job_name=dictt['table'][i]['job_name'].strip(), item=itemm,
                                       quantity=dictt['table'][i]['quantity'], unit=dictt['table'][i]['unit'],
                                       rate=dictt['table'][i]['rate'],
                                       amount=(float(dictt['table'][i]['rate']) * float(dictt['table'][i]['quantity'])))
                        except:
                            job = pjob(job_id=dictt['table'][i]['serial'], slip_no=dictt['table'][i]['slip_no'],
                                       gst=dictt['table'][i]['gst'], challan_no=challan_no, job_date=datetime.strptime(
                                    dictt['table'][i]['job_date'].replace(',', '').replace('.', ''), '%B %d %Y %I %p'),
                                       job_name=dictt['table'][i]['job_name'].strip(), item=itemm,
                                       quantity=dictt['table'][i]['quantity'], unit=dictt['table'][i]['unit'],
                                       rate=dictt['table'][i]['rate'],
                                       amount=(float(dictt['table'][i]['rate']) * float(dictt['table'][i]['quantity'])))
                sum += float(job.gst) + job.amount
                job.save()
            if (abs(int(sum) - int(float(challan.total_amount))) > 2):
                raise Exception('The total amount is wrong please try again')
        print('It was successfully')
        pdf = pchallan_pdf(challan.challan_no)
        pdf_mime = MIMEApplication(pdf, _subtype='pdf')
        pdf_mime.add_header('content-disposition', 'attachment')
        email = EmailMessage(
            'Challan No.: {0} Modified'.format(challan.challan_no),
            'Please find an attachment to the challan from pkscan graphics accounts',
            'pkscan.acc@gmail.com',
            [clientt.email],
            [],
            reply_to=[],
            headers={'Message-ID': 'foo'},
            attachments=[pdf_mime]
        )
        email.send()
        http = HttpResponse(pdf, content_type='application/pdf')
        http['Content-Disposition'] = 'inline; filename="challan.pdf"'
        l = logs(user_name=str(request.user),
                 message="Modified a challan(Print) for " + str(dictt['client_name']) + " with challan no " + str(
                     challan.challan_no) + ".")
        l.save()
        return http
    except Exception as e:
        print(e)
        if (str(e) == 'The total amount is wrong please try again'):
            return render(request, 'pchallan_modify.html', {"items": item, "clients": clients, 'datetime': dt,
                                                            'error_message': "The total amount is wrong please try again", })
        print(e.__class__.__name__)
        if (str(e.__class__.__name__) == 'DataError'):
            return render(request, 'pchallan_modify.html',
                          {"pchallans": pchallans, "items": item, "clients": clients, 'datetime': dt,
                           'error_message': "Please provide the data correctly", })
        if (str(e.__class__.__name__) == 'ValidationError'):
            return render(request, 'pchallan_modify.html',
                          {"pchallans": pchallans, "items": item, "clients": clients, 'datetime': dt,
                           'error_message': "Please provide the data correctly", })
        else:
            return render(request, 'pchallan_modify.html',
                          {"pchallans": pchallans, "items": item, "clients": clients, 'datetime': dt,
                           'error_message': "Some error occured", })


@login_required
def bill_modify_pchallan(request):
    item = list(items.objects.all().order_by('item_name'))
    clients = list(client.objects.all().order_by('client_name'))
    pchallans = list(pchallan.objects.filter(deleted=False).filter(single_bill=True).order_by('challan_no'))
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    dt = dt.split(" ")[0] + "T" + dt.split(" ")[1]
    check_user = Employee.objects.get(user=user.objects.get(username=request.user))

    if (check_user.role != 'Admin'):
        return render(request, 'pchallan_modify.html',
                      {"pchallans": pchallans, "items": item, "clients": clients, 'datetime': dt,
                       'error_message': "You dont have the permission to modify anything", })
    try:
        data = json.loads(request.body)
        dictt = {}
        for i in range(len(data)):
            dictt[list(data[i].items())[0][0]] = list(data[i].items())[0][1]
        table = []
        for i in range(len(dictt['table'])):
            row = {}
            for j in range(len(dictt['table'][i]['value'])):
                row['serial'] = dictt['table'][i]['key']
                row[list(dictt['table'][i]['value'][j].items())[0][0]] = list(dictt['table'][i]['value'][j].items())[0][
                    1]
            table.append(row)
        dictt['table'] = table
        with transaction.atomic():
            clientt = get_object_or_404(client, pk=dictt['client_name'])
            challan = pchallan.objects.filter(bill_no=dictt['bill_no'])[0]
            if (challan.payment_no != None):
                return render(request, 'pchallan_bill_modify.html',
                              {"pchallans": pchallans, "items": item, "clients": clients, 'datetime': dt,
                               'error_message': "You can't modify a paid challan", })
            dictt['date'] = dictt['date'].replace('T', ' ')
            challan.date = datetime.strptime(dictt['date'], '%Y-%m-%d %H:%M:%S')
            challan.client_name = clientt
            challan.gross_amount = dictt['gross_amount']
            challan.other_amount = dictt['other_amount']
            challan.total_amount = dictt['total_amount']
            challan.gst = dictt['gst']
            challan.deleted = False
            challan.save()
            bil = get_object_or_404(bill, pk=challan.bill_no.bill_no)
            bil.date = datetime.strptime(dictt['date'], '%Y-%m-%d %H:%M:%S')
            bil.client_name = clientt
            bil.gross_amount = dictt['gross_amount']
            bil.other_amount = dictt['other_amount']
            bil.total_amount = dictt['total_amount']
            bil.gst = dictt['gst']
            bil.deleted = False
            bil.save()
            print(dictt['table'])
            try:
                print("challan no ", challan.challan_no)
            except:
                pass
            pjobs = pjob.objects.all().filter(challan_no=challan.challan_no)
            for pj in pjobs:
                pj.delete()
            sum = 0
            for i in range(len(dictt['table'])):
                itemm = get_object_or_404(items, pk=dictt['table'][i]['item'])
                challan_no = get_object_or_404(pchallan, pk=challan.challan_no)
                try:
                    job = pjob(job_id=dictt['table'][i]['serial'], slip_no=dictt['table'][i]['slip_no'],
                               gst=dictt['table'][i]['gst'], challan_no=challan_no, job_date=datetime.strptime(
                            dictt['table'][i]['job_date'].replace(',', '').replace('.', ''), '%b %d %Y %I:%M %p'),
                               job_name=dictt['table'][i]['job_name'].strip(), item=itemm,
                               quantity=dictt['table'][i]['quantity'], unit=dictt['table'][i]['unit'],
                               rate=dictt['table'][i]['rate'],
                               amount=(float(dictt['table'][i]['rate']) * float(dictt['table'][i]['quantity'])))
                except:
                    try:
                        job = pjob(job_id=dictt['table'][i]['serial'], slip_no=dictt['table'][i]['slip_no'],
                                   gst=dictt['table'][i]['gst'], challan_no=challan_no,
                                   job_date=datetime.strptime(dictt['table'][i]['job_date'].replace('T', ' '),
                                                              '%Y-%m-%d %H:%M:%S'),
                                   job_name=dictt['table'][i]['job_name'].strip(), item=itemm,
                                   quantity=dictt['table'][i]['quantity'], unit=dictt['table'][i]['unit'],
                                   rate=dictt['table'][i]['rate'],
                                   amount=(float(dictt['table'][i]['rate']) * float(dictt['table'][i]['quantity'])))
                    except:
                        try:
                            job = pjob(job_id=dictt['table'][i]['serial'], slip_no=dictt['table'][i]['slip_no'],
                                       gst=dictt['table'][i]['gst'], challan_no=challan_no, job_date=datetime.strptime(
                                    dictt['table'][i]['job_date'].replace(',', '').replace('.', ''),
                                    '%B %d %Y %I:%M %p'), job_name=dictt['table'][i]['job_name'].strip(), item=itemm,
                                       quantity=dictt['table'][i]['quantity'], unit=dictt['table'][i]['unit'],
                                       rate=dictt['table'][i]['rate'],
                                       amount=(float(dictt['table'][i]['rate']) * float(dictt['table'][i]['quantity'])))
                        except:
                            job = pjob(job_id=dictt['table'][i]['serial'], slip_no=dictt['table'][i]['slip_no'],
                                       gst=dictt['table'][i]['gst'], challan_no=challan_no, job_date=datetime.strptime(
                                    dictt['table'][i]['job_date'].replace(',', '').replace('.', ''), '%B %d %Y %I %p'),
                                       job_name=dictt['table'][i]['job_name'].strip(), item=itemm,
                                       quantity=dictt['table'][i]['quantity'], unit=dictt['table'][i]['unit'],
                                       rate=dictt['table'][i]['rate'],
                                       amount=(float(dictt['table'][i]['rate']) * float(dictt['table'][i]['quantity'])))
                sum += float(job.gst) + job.amount
                job.save()
            if (abs(int(sum) - int(float(challan.total_amount))) > 2):
                raise Exception('The total amount is wrong please try again')
        print('It was successfully')
        pdf = bill_pdf(bil.bill_no)
        pdf_mime = MIMEApplication(pdf, _subtype='pdf')
        pdf_mime.add_header('content-disposition', 'attachment')
        email = EmailMessage(
            'Bill No.: {0} Modified'.format(bil.bill_no),
            'Please find an attachment to the bill from pkscan graphics accounts',
            'pkscan.acc@gmail.com',
            [clientt.email],
            [],
            reply_to=[],
            headers={'Message-ID': 'foo'},
            attachments=[pdf_mime]
        )
        email.send()
        http = HttpResponse(pdf, content_type='application/pdf')
        http['Content-Disposition'] = 'inline; filename="challan.pdf"'
        l = logs(user_name=str(request.user),
                 message="Modified a bill(Print) for " + str(dictt['client_name']) + " with bill no " + str(
                     bil.bill_no) + ".")
        l.save()
        return http
    except Exception as e:
        print(e)
        if (str(e) == 'The total amount is wrong please try again'):
            return render(request, 'pchallan_add.html', {"items": item, "clients": clients, 'datetime': dt,
                                                         'error_message': "The total amount is wrong please try again", })
        print(e.__class__.__name__)
        if (str(e.__class__.__name__) == 'DataError'):
            return render(request, 'pchallan_bill_modify.html',
                          {"pchallans": pchallans, "items": item, "clients": clients, 'datetime': dt,
                           'error_message': "Please provide the data correctly", })
        if (str(e.__class__.__name__) == 'ValidationError'):
            return render(request, 'pchallan_bill_modify.html',
                          {"pchallans": pchallans, "items": item, "clients": clients, 'datetime': dt,
                           'error_message': "Please provide the data correctly", })
        else:
            return render(request, 'pchallan_bill_modify.html',
                          {"pchallans": pchallans, "items": item, "clients": clients, 'datetime': dt,
                           'error_message': "Some error occured", })


@login_required
def delete_pchallan(request):
    pchallans = list(pchallan.objects.filter(deleted=False).filter(bill_no=None).order_by('challan_no'))
    check_user = Employee.objects.get(user=user.objects.get(username=request.user))
    if (check_user.role != 'Admin'):
        return render(request, 'pchallan_delete.html',
                      {"pchallans": pchallans, 'error_message': "You dont have the permission to modify anything", })
    try:
        with transaction.atomic():
            try:
                selected_choice = pchallan.objects.get(pk=request.POST['challan_no'])
            except (KeyError, items.DoesNotExist):
                return render(request, 'pchallan_delete.html', {"pchallans": pchallans,
                                                                'error_message': "The item group name provided has not been added", })
            selected_choice.deleted = True
            selected_choice.save()
            selected_choice.client_name.balance = selected_choice.client_name.balance + selected_choice.recieved
            selected_choice.client_name.save()
            pchallans = list(pchallan.objects.filter(deleted=False).filter(bill_no=None).order_by('challan_no'))
            pchallans_json = serializers.serialize('json', pchallans)
            l = logs(user_name=str(request.user), message="Deleted a challan(Print) for " + str(
                selected_choice.client_name.client_name) + " with challan no " + str(request.POST['challan_no']) + ".")
            l.save()
            return render(request, 'pchallan_delete.html', {"pchallans": pchallans, "pchallans_json": pchallans_json,
                                                            'success_message': "Item Group deleted successfully", })
    except Exception as e:
        print(e)
        print(e.__class__.__name__)
        if (str(e.__class__.__name__) == 'DataError'):
            return render(request, 'pchallan_delete.html',
                          {"pchallans": pchallans, 'error_message': "Please provide the data correctly", })
        if (str(e.__class__.__name__) == 'ValidationError'):
            return render(request, 'pchallan_delete.html',
                          {"pchallans": pchallans, 'error_message': "Please provide the data correctly", })
        else:
            return render(request, 'pchallan_delete.html',
                          {"pchallans": pchallans, 'error_message': "Some error occured", })


def last_balance(cl_name):
    pchals = pchallan.objects.filter(client_name=cl_name).filter(deleted=False)
    fchals = fchallan.objects.filter(client_name=cl_name).filter(deleted=False)
    cl = client.objects.get(pk=cl_name)
    bal = 0
    for each in pchals:
        bal += each.total_amount - each.recieved
    print('bal after pchals', bal)
    for each in fchals:
        bal += each.total_amount - each.recieved
    print('bal after fchals', bal)
    bal = bal - cl.balance
    return bal


def pchallan_pdf(chal_no):
    challan = get_object_or_404(pchallan, pk=chal_no)
    jobs = pjob.objects.filter(challan_no=chal_no)
    jobs = sorted(jobs, key=lambda instance: instance.job_id)
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
    cnvs.drawString(11 * mm, A5[1] - 100, 'Challan No.    ' + str(challan.challan_no))
    cnvs.setFont('Helvetica-Bold', 12)
    cnvs.drawString(11 * mm, A5[1] - 115, 'Party    ' + str(challan.client_name.client_name))
    cnvs.setFont('Helvetica', 10)
    cnvs.drawString(11 * mm, A5[1] - 130, 'Phone No.    ' + str(challan.client_name.phone1))
    cnvs.drawString(90 * mm, A5[1] - 100, 'Date    ' + str(challan.date.strftime('%d/%m/%Y')))
    cnvs.line(5 * mm, A5[1] - 133, 141 * mm, A5[1] - 133)
    cnvs.line(5 * mm, A5[1] - 153, 141 * mm, A5[1] - 153)
    cnvs.setFont('Helvetica-Bold', 10)
    cnvs.drawString(100 * mm, A5[1] - 540, 'For PK Scan Graphics')
    cnvs.setFont('Helvetica', 10)
    cnvs.line(123 * mm, A5[1] - 530, 141 * mm, A5[1] - 530)
    cnvs.line(123 * mm, A5[1] - 529, 141 * mm, A5[1] - 529)
    cnvs.drawString(121 * mm - stringWidth('Total Balance', 'Helvetica', 10), A5[1] - 525, 'Total Balance')
    cnvs.drawString(140 * mm - stringWidth(str(round(last_balance(challan.client_name.client_name) - (
            challan.total_amount - challan.recieved) + challan.total_amount, 2)), 'Helvetica', 10), A5[1] - 525,
                    str(round(last_balance(challan.client_name.client_name) - (
                            challan.total_amount - challan.recieved) + challan.total_amount, 2)))
    cnvs.line(123 * mm, A5[1] - 514, 141 * mm, A5[1] - 514)
    cnvs.drawString(121 * mm - stringWidth('Last Balance', 'Helvetica', 10), A5[1] - 510, 'Last Balance')
    cnvs.drawString(140 * mm - stringWidth(
        str(round(last_balance(challan.client_name.client_name) - (challan.total_amount - challan.recieved), 2)),
        'Helvetica', 10), A5[1] - 510, str(
        round(last_balance(challan.client_name.client_name) - (challan.total_amount - challan.recieved), 2)))
    cnvs.drawString(121 * mm - stringWidth('Balance', 'Helvetica', 10), A5[1] - 498, 'Balance')
    cnvs.drawString(140 * mm - stringWidth(str(round(challan.total_amount - challan.recieved, 2)), 'Helvetica', 10),
                    A5[1] - 498, str(round(challan.total_amount - challan.recieved, 2)))
    cnvs.line(123 * mm, A5[1] - 487, 141 * mm, A5[1] - 487)
    cnvs.drawString(121 * mm - stringWidth('Recieved Amount', 'Helvetica', 10), A5[1] - 481, 'Recieved Amount')
    cnvs.drawString(140 * mm - stringWidth(str(round(challan.recieved, 2)), 'Helvetica', 10), A5[1] - 481,
                    str(round(challan.recieved, 2)))
    cnvs.drawString(121 * mm - stringWidth('Bill Amount', 'Helvetica', 10), A5[1] - 469, 'Bill Amount')
    cnvs.drawString(140 * mm - stringWidth(str(round(challan.total_amount, 2)), 'Helvetica', 10), A5[1] - 469,
                    str(round(challan.total_amount, 2)))
    cnvs.line(123 * mm, A5[1] - 459, 141 * mm, A5[1] - 459)
    cnvs.drawString(121 * mm - stringWidth('TAX', 'Helvetica', 10), A5[1] - 457, 'TAX')
    cnvs.drawString(140 * mm - stringWidth(str(round(challan.gst, 2)), 'Helvetica', 10), A5[1] - 457,
                    str(round(challan.gst, 2)))
    cnvs.drawString(121 * mm - stringWidth('Gross Amount', 'Helvetica', 10), A5[1] - 445, 'Gross Amount')
    cnvs.drawString(140 * mm - stringWidth(str(round(challan.gross_amount, 2)), 'Helvetica', 10), A5[1] - 445,
                    str(round(challan.gross_amount, 2)))
    cnvs.line(5 * mm, A5[1] - 433, 141 * mm, A5[1] - 433)
    cnvs.line(123 * mm, A5[1] - 133, 123 * mm, A5[1] - 530)
    cnvs.line(112 * mm, A5[1] - 133, 112 * mm, A5[1] - 433)
    cnvs.line(103 * mm, A5[1] - 133, 103 * mm, A5[1] - 433)
    cnvs.line(46 * mm, A5[1] - 133, 46 * mm, A5[1] - 433)
    cnvs.line(28 * mm, A5[1] - 133, 28 * mm, A5[1] - 433)
    cnvs.line(15 * mm, A5[1] - 133, 15 * mm, A5[1] - 433)
    cnvs.drawString(8 * mm, A5[1] - 146, 'No.')
    cnvs.drawString(16 * mm, A5[1] - 146, 'Slip No.')
    cnvs.drawString(30 * mm, A5[1] - 146, 'Job Date')
    cnvs.drawString(55 * mm, A5[1] - 146, 'D E S C R I P T I O N')
    cnvs.drawString(104 * mm, A5[1] - 146, 'Qty.')
    cnvs.drawString(114 * mm, A5[1] - 146, 'Rate')
    cnvs.drawString(126 * mm, A5[1] - 146, 'Amount')
    cnvs.setFont('Helvetica-Bold', 12)
    cnvs.drawString(13 * mm, A5[1] - 510, 'Terms and Conditions:')
    cnvs.setFont('Helvetica', 10)
    cnvs.drawString(13 * mm, A5[1] - 522, 'Please check Film before use.')
    cnvs.drawString(13 * mm, A5[1] - 534, 'We will be not responsible for any corrections.')
    cnvs.setFont('Helvetica', 9)
    first = 165
    for i in range(len(jobs)):
        cnvs.drawString(8 * mm, A5[1] - first - (13 * i), str(jobs[i].job_id))
        cnvs.drawString(21 * mm, A5[1] - first - (13 * i), str(jobs[i].slip_no))
        cnvs.drawString(29 * mm, A5[1] - first - (13 * i), str(jobs[i].job_date.strftime('%d/%m/%Y')))
        cnvs.drawString(48 * mm, A5[1] - first - (13 * i), (jobs[i].job_name + " -:- " + jobs[i].item.item_name))
        cnvs.drawString(104 * mm, A5[1] - first - (13 * i), str(jobs[i].quantity))
        cnvs.drawString(114 * mm, A5[1] - first - (13 * i), str(round(jobs[i].rate, 2)))
        cnvs.drawString(126 * mm, A5[1] - first - (13 * i), str(round(jobs[i].amount, 2)))
    cnvs.showPage
    cnvs.save()
    pdf = buffer.getvalue()

    buffer.close()
    return pdf


from reportlab.lib.pagesizes import A4
from num2words import num2words
from fchallan.models import fjob


def bill_pdf(bil_no, original=False):
    bil = bill.objects.get(pk=bil_no)
    challansp = pchallan.objects.filter(bill_no=bil_no)
    challansf = fchallan.objects.filter(bill_no=bil_no)
    jobs = []
    for each in challansp:
        jobs.extend(pjob.objects.filter(challan_no=each.challan_no))
    for each in challansf:
        jobs.extend(fjob.objects.filter(challan_no=each.challan_no))
    jobs = sorted(jobs, key=lambda instance: instance.job_date)
    buffer = BytesIO()
    cnvs = canvas.Canvas(buffer, pagesize=A4)
    cnvs.setFont('Helvetica', 12)
    cnvs.translate(mm, mm)
    cnvs.rect(10 * mm, 10 * mm, 190 * mm, 247 * mm, stroke=1, fill=0)
    cnvs.setFont('Helvetica-Bold', 14)
    if (original):
        cnvs.drawString((190 - stringWidth('Original', 'Helvetica-Bold', 14)), A4[1] - 40, '')
    else:
        cnvs.drawString((190 - stringWidth('Duplicate', 'Helvetica-Bold', 14)), A4[1] - 40, '')
    cnvs.drawString((A4[0] - stringWidth('TAX INVOICE', 'Helvetica-Bold', 14)) / 2, A4[1] - 40, 'TAX INVOICE')
    cnvs.setFont('Helvetica-Bold', 14)
    cnvs.drawString((A4[0] - stringWidth('PK Scan Graphics', 'Helvetica-Bold', 14)) / 2, A4[1] - 55, 'PK Scan Graphics')
    cnvs.setFont('Helvetica', 12)
    cnvs.drawString(
        (A4[0] - stringWidth('4206, Hansa Puri Road, Budh Nagar, Tri Nagar, New Delhi-110035', 'Helvetica', 12)) / 2,
        A4[1] - 70, '4206, Hansa Puri Road, Budh Nagar, Tri Nagar, New Delhi-110035')
    cnvs.drawString((A4[0] - stringWidth('Phone : 9313131113', 'Helvetica', 12)) / 2, A4[1] - 85, 'Phone : 9313131113')
    cnvs.drawString((A4[0] - stringWidth('Date : 10/12/2018', 'Helvetica', 12)) / 2, A4[1] - 100,
                    'Date : ' + bil.date.strftime('%d/%m/%Y'))
    cnvs.drawString(10 * mm, A4[1] - 110, 'Bill No : ' + str(bil_no))
    cnvs.setFont('Helvetica-Bold', 14)
    cnvs.drawString(135 * mm, A4[1] - 110, 'GSTIN : 07AGCPK2843D1ZS')
    cnvs.setFont('Helvetica', 10)
    cnvs.drawString(12 * mm, A4[1] - 130, 'Billing to')
    cnvs.setFont('Helvetica-Bold', 12)
    cnvs.drawString(12 * mm, A4[1] - 145, str(bil.client_name.client_name))
    cnvs.setFont('Helvetica', 10)
    address = str(bil.client_name.address)
    address2 = ''
    while (stringWidth(address, 'Helvetica', 10) > 250):
        address2 = address2 + ' ' + address.split(' ')[-1]
        address = ' '.join(address.split(' ')[:-1])
    cnvs.drawString(12 * mm, A4[1] - 170, str(address))
    cnvs.drawString(12 * mm, A4[1] - 185, str(address2 + ', ' + bil.client_name.city))
    cnvs.drawString(12 * mm, A4[1] - 205, str(bil.client_name.state))
    cnvs.line(105 * mm, 257 * mm, 105 * mm, A4[1] - 250)
    cnvs.drawString(107 * mm, A4[1] - 130, 'Delivered to')
    cnvs.drawString(107 * mm, A4[1] - 170, str(address))
    cnvs.drawString(107 * mm, A4[1] - 185, str(address2 + ', ' + bil.client_name.city))
    cnvs.line(10 * mm, A4[1] - 210, 200 * mm, A4[1] - 210)
    cnvs.line(10 * mm, A4[1] - 230, 200 * mm, A4[1] - 230)
    cnvs.line(57.5 * mm, A4[1] - 210, 57.5 * mm, A4[1] - 230)
    cnvs.line(152.5 * mm, A4[1] - 210, 152.5 * mm, A4[1] - 230)
    cnvs.drawString(12 * mm, A4[1] - 224, 'GSTIN')
    cnvs.drawString(12 * mm, A4[1] - 244, str(bil.client_name.gstin))
    cnvs.drawString(59.5 * mm, A4[1] - 224, 'State Name - Code')
    cnvs.drawString(59.5 * mm, A4[1] - 244, str(bil.client_name.state))
    cnvs.drawString(107 * mm, A4[1] - 224, 'GSTIN')
    cnvs.drawString(107 * mm, A4[1] - 244, str(bil.client_name.gstin))
    cnvs.drawString(154.5 * mm, A4[1] - 224, 'State Name - Code')
    cnvs.drawString(154.5 * mm, A4[1] - 244, str(bil.client_name.state))
    cnvs.line(10 * mm, A4[1] - 250, 200 * mm, A4[1] - 250)
    cnvs.line(57.5 * mm, A4[1] - 230, 57.5 * mm, A4[1] - 250)
    cnvs.line(152.5 * mm, A4[1] - 230, 152.5 * mm, A4[1] - 250)
    cnvs.line(10 * mm, A4[1] - 280, 200 * mm, A4[1] - 280)
    cnvs.line(20 * mm, A4[1] - 250, 20 * mm, A4[1] - 650)
    cnvs.line(95 * mm, A4[1] - 250, 95 * mm, A4[1] - 650)
    cnvs.line(110 * mm, A4[1] - 250, 110 * mm, A4[1] - 650)
    cnvs.line(130 * mm, A4[1] - 250, 130 * mm, A4[1] - 650)
    cnvs.line(145 * mm, A4[1] - 250, 145 * mm, A4[1] - 745)
    cnvs.line(160 * mm, A4[1] - 250, 160 * mm, A4[1] - 650)
    cnvs.line(175 * mm, A4[1] - 250, 175 * mm, A4[1] - 745)
    cnvs.drawString(12 * mm, A4[1] - 267, 'No.')
    cnvs.drawString(40 * mm, A4[1] - 267, 'D E S C R I P T I O  N')
    cnvs.drawString(98 * mm, A4[1] - 263, 'HSN')
    cnvs.drawString(98 * mm, A4[1] - 273, 'Code')
    cnvs.drawString(117 * mm, A4[1] - 267, 'Qty')
    cnvs.drawString(134 * mm, A4[1] - 267, 'Unit')
    cnvs.drawString(148 * mm, A4[1] - 267, 'Tax %')
    cnvs.drawString(164 * mm, A4[1] - 267, 'Rate')
    cnvs.drawString(180 * mm, A4[1] - 267, 'Amount')
    cnvs.line(10 * mm, A4[1] - 745, 200 * mm, A4[1] - 745)
    cnvs.setFont('Helvetica', 5)
    cnvs.drawString(11 * mm, A4[1] - 805, '6. This is a computer genertated bill')
    cnvs.drawString(11 * mm, A4[1] - 797, '5. Payment to be made immediately at the time of delivery or goods.')
    cnvs.drawString(11 * mm, A4[1] - 789, '4. All disputes are subject to Delhi jurisdiction')
    cnvs.drawString(11 * mm, A4[1] - 781, '3. Our risk or responsiblity cease once the delivery is affected.')
    cnvs.drawString(11 * mm, A4[1] - 773, '2. Once sold, goods will not be taken back / return.')
    cnvs.drawString(11 * mm, A4[1] - 765, '1. E. &. O.E.')
    cnvs.setFont('Helvetica-Bold', 8)
    cnvs.drawString(11 * mm, A4[1] - 755, 'Terms and conditions')
    cnvs.setFont('Helvetica-Bold', 10)
    cnvs.drawString(11 * mm, A4[1] - 740, 'IFSC Code     CNRB0002016')
    cnvs.drawString(11 * mm, A4[1] - 728, 'Account No.  2016201002902')
    cnvs.drawString(11 * mm, A4[1] - 716, 'Branch           Keshav Puram')
    cnvs.drawString(11 * mm, A4[1] - 704, 'Bank Name    Canara Bank')
    if ('delhi' in bil.client_name.state.lower()):
        cnvs.drawString(170 * mm - stringWidth('Total', 'Helvetica-Bold', 10), A4[1] - 664, 'Total')
        cnvs.drawString(170 * mm - stringWidth('SGST', 'Helvetica-Bold', 10), A4[1] - 682, 'SGST')
        cnvs.drawString(170 * mm - stringWidth('CGST', 'Helvetica-Bold', 10), A4[1] - 700, 'CGST')
        cnvs.drawString(170 * mm - stringWidth('Adjustment', 'Helvetica-Bold', 10), A4[1] - 718, 'Adjustment')
        cnvs.drawString(170 * mm - stringWidth('Invoice Total', 'Helvetica-Bold', 10), A4[1] - 738, 'Invoice Total')
        cnvs.drawString(199 * mm - stringWidth(str(round(bil.gross_amount, 2)), 'Helvetica-Bold', 10), A4[1] - 664,
                        str(round(bil.gross_amount, 2)))
        cnvs.drawString(199 * mm - stringWidth(str(round(bil.gst / 2, 2)), 'Helvetica-Bold', 10), A4[1] - 682,
                        str(round(bil.gst / 2, 2)))
        cnvs.drawString(199 * mm - stringWidth(str(round(bil.gst / 2, 2)), 'Helvetica-Bold', 10), A4[1] - 700,
                        str(round(bil.gst / 2, 2)))
        adjustment = round(bil.total_amount, 0) - round(bil.gross_amount, 2) - 2 * round(bil.gst / 2, 2)
        if adjustment < 0:
            cnvs.drawString(199 * mm - stringWidth(str(adjustment), 'Helvetica-Bold', 10), A4[1] - 718,
                            str(adjustment))
        else:
            cnvs.drawString(199 * mm - stringWidth("+" + str(adjustment), 'Helvetica-Bold', 10), A4[1] - 718,
                            "+" + str(adjustment))
        cnvs.drawString(199 * mm - stringWidth(str(round(bil.total_amount, 0)), 'Helvetica-Bold', 10), A4[1] - 738,
                        str(round(bil.total_amount, 0)))

        cnvs.line(175 * mm, A4[1] - 724, 200 * mm, A4[1] - 724)
        cnvs.line(175 * mm, A4[1] - 706, 200 * mm, A4[1] - 706)
        cnvs.line(175 * mm, A4[1] - 688, 200 * mm, A4[1] - 688)
        cnvs.line(175 * mm, A4[1] - 668, 200 * mm, A4[1] - 668)
    else:
        cnvs.drawString(170 * mm - stringWidth('Total', 'Helvetica-Bold', 10), A4[1] - 664, 'Total')
        cnvs.drawString(170 * mm - stringWidth('SGST', 'Helvetica-Bold', 10), A4[1] - 682, 'IGST')
        cnvs.drawString(170 * mm - stringWidth('Adjustment', 'Helvetica-Bold', 10), A4[1] - 700, 'Adjustment')
        cnvs.drawString(170 * mm - stringWidth('Invoice Total', 'Helvetica-Bold', 10), A4[1] - 738, 'Invoice Total')
        cnvs.drawString(199 * mm - stringWidth(str(round(bil.gross_amount, 2)), 'Helvetica-Bold', 10), A4[1] - 664,
                        str(round(bil.gross_amount, 2)))
        cnvs.drawString(199 * mm - stringWidth(str(round(bil.gst, 2)), 'Helvetica-Bold', 10), A4[1] - 682,
                        str(round(bil.gst, 2)))
        adjustment = round(bil.total_amount, 0) - round(bil.gross_amount, 2) - round(bil.gst, 2)
        if adjustment < 0:
            cnvs.drawString(199 * mm - stringWidth(str(adjustment), 'Helvetica-Bold', 10), A4[1] - 700,
                            str(adjustment))
        else:
            cnvs.drawString(199 * mm - stringWidth("+" + str(adjustment), 'Helvetica-Bold', 10), A4[1] - 700,
                            "+" + str(adjustment))
        cnvs.drawString(199 * mm - stringWidth(str(round(bil.total_amount, 0)), 'Helvetica-Bold', 10), A4[1] - 738,
                        str(round(bil.total_amount, 0)))
        cnvs.line(175 * mm, A4[1] - 706, 200 * mm, A4[1] - 706)
        cnvs.line(175 * mm, A4[1] - 688, 200 * mm, A4[1] - 688)
        cnvs.line(175 * mm, A4[1] - 668, 200 * mm, A4[1] - 668)
    cnvs.line(10 * mm, A4[1] - 650, 200 * mm, A4[1] - 650)
    cnvs.setFont('Helvetica', 10)
    cnvs.drawString(11 * mm, A4[1] - 684, 'In Words : ' + num2words(round(bil.total_amount, 0), lang='en_IN'))
    cnvs.setFont('Helvetica-Bold', 10)
    cnvs.drawString(160 * mm, A4[1] - 755, 'For PK Scan Graphics')
    cnvs.drawString(173 * mm, A4[1] - 810, 'Auth Signatory')
    cnvs.setFont('Helvetica', 9)
    serial = 1
    first = 295
    for i in range(len(jobs)):
        cnvs.drawString(12 * mm, A4[1] - first - (12 * i), str(serial))
        try:
            cnvs.drawString(22 * mm, A4[1] - first - (12 * i), (
                    str(jobs[i].item.item_name) + ', Job- ' + str(jobs[i].job_name) + ', Size- ' + str(round(
                jobs[i].width, 1)) + ' x ' + str(round(jobs[i].height, 1)) + ', Set- ' + str(jobs[i].quantity)))
        except:
            cnvs.drawString(22 * mm, A4[1] - first - (12 * i),
                            (str(jobs[i].item.item_name) + ', Job- ' + str(jobs[i].job_name)))
        cnvs.drawString(97 * mm, A4[1] - first - (12 * i), jobs[i].item.group_name.hsn_code)
        try:
            cnvs.drawString(112 * mm, A4[1] - first - (12 * i), str(round(jobs[i].width * jobs[i].height * jobs[i].quantity, 2)))
        except:
            cnvs.drawString(110 * mm, A4[1] - first - (12 * i), str(round(jobs[i].quantity, 2)))
        cnvs.drawString(132 * mm, A4[1] - first - (12 * i), str(jobs[i].unit))
        cnvs.drawString(147 * mm, A4[1] - first - (12 * i), str(round(jobs[i].item.group_name.tax, 2)))
        cnvs.drawString(173 * mm - stringWidth(str(round(jobs[i].rate, 2)), 'Helvetica', 9), A4[1] - first - (12 * i),
                        str(round(jobs[i].rate, 2)))
        cnvs.drawString(196 * mm - stringWidth(str(round(jobs[i].amount, 2)), 'Helvetica', 9), A4[1] - first - (12 * i),
                        str(round(jobs[i].amount, 2)))
        serial += 1
    cnvs.showPage()
    cnvs.save()
    pdf = buffer.getvalue()

    buffer.close()
    return pdf
