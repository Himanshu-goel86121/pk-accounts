import json
# Create your views here.
from datetime import datetime
from email.mime.application import MIMEApplication
from io import BytesIO

from client.models import client
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User as user
from django.core import serializers
from django.core.mail import EmailMessage
from django.db import transaction
from django.db.models import Max
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from fchallan.models import fchallan, fjob
from items.models import items
from itertools import chain
from logs.models import logs
from pchallan.models import pchallan, pjob
from users.models import Employee

from .models import bill


# Create your views here.
@login_required
def get_challans(request):
    clients = list(client.objects.all().order_by('client_name'))
    print(request.POST['client'])
    pchallans = list(
        pchallan.objects.filter(client_name=request.POST['client']).filter(bill_no=None).filter(deleted=False))
    fchallans = list(
        fchallan.objects.filter(client_name=request.POST['client']).filter(bill_no=None).filter(deleted=False))
    return render(request, "bill_add.html",
                  {"pchallans": pchallans, "fchallans": fchallans, "datetime_chosen": request.POST['date'],
                   "client_chosen": request.POST['client'], "clients": clients})


@login_required
def bill_add(request):
    clients = list(client.objects.all().order_by('client_name'))
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    dt = dt.split(" ")[0] + "T" + dt.split(" ")[1]
    return render(request, "bill_add.html", {"clients": clients, "datetime": dt})


@login_required
def get_jobs(request):
    data = json.loads(request.body)
    dictt = {}
    for i in range(len(data)):
        dictt[list(data[i].items())[0][0]] = list(data[i].items())[0][1]
    if (dictt['type'] == 'Printout'):
        jobs = list(pjob.objects.filter(challan_no=dictt['challan_no']))
    if (dictt['type'] == 'Film'):
        jobs = list(fjob.objects.filter(challan_no=dictt['challan_no']))
        for each in jobs:
            each.quantity = each.width * each.height * each.quantity
    jobs = serializers.serialize('json', jobs)
    return HttpResponse(jobs)


@login_required
def bill_delete(request):
    bills = list(bill.objects.filter(deleted=False).filter(payment_no=None).order_by('bill_no'))
    bills_json = serializers.serialize('json', bills)
    return render(request, "bill_delete.html", {"bills": bills, "bills_json": bills_json})


@login_required
def bill_print(request):
    bills = list(bill.objects.filter(deleted=False))
    return render(request, "bill_print.html", {"bills": bills})


@login_required
def bill_display(request):
    bills = list(bill.objects.filter(deleted=False).order_by('bill_no'))
    for bil in bills:
        chal1 = fchallan.objects.filter(bill_no=bil.bill_no)
        chal2 = pchallan.objects.filter(bill_no=bil.bill_no)
        for chal in chal1:
            chal.challan_no = str(chal.challan_no) + ' - F'
        for chal in chal2:
            chal.challan_no = str(chal.challan_no) + ' - P'
        chals = list(chain(chal1, chal2))
        bill_chal_no = []
        for chal in chals:
            bill_chal_no.append(chal.challan_no)
        bil.chals = ','.join(bill_chal_no)
    clients = list(client.objects.all().order_by('client_name'))
    return render(request, "bill_get.html", {"bills": bills, "clients": clients})


@login_required
def filter_date(request):
    bills = list(
        bill.objects.filter(deleted=False).filter(date__range=(request.POST['from'], request.POST['to'])).order_by(
            'bill_no'))
    for bil in bills:
        chal1 = fchallan.objects.filter(bill_no=bil.bill_no)
        chal2 = pchallan.objects.filter(bill_no=bil.bill_no)
        for chal in chal1:
            chal.challan_no = str(chal.challan_no) + ' - F'
        for chal in chal2:
            chal.challan_no = str(chal.challan_no) + ' - P'
        chals = list(chain(chal1, chal2))
        bill_chal_no = []
        for chal in chals:
            bill_chal_no.append(chal.challan_no)
        bil.chals = ','.join(bill_chal_no)
    clients = list(client.objects.all().order_by('client_name'))
    return render(request, "bill_get.html", {"bills": bills, "clients": clients})


@login_required
def filter_client(request):
    bills = list(bill.objects.filter(deleted=False).filter(client_name=request.POST['client_name']).order_by('bill_no'))
    for bil in bills:
        chal1 = fchallan.objects.filter(bill_no=bil.bill_no)
        chal2 = pchallan.objects.filter(bill_no=bil.bill_no)
        for chal in chal1:
            chal.challan_no = str(chal.challan_no) + ' - F'
        for chal in chal2:
            chal.challan_no = str(chal.challan_no) + ' - P'
        chals = list(chain(chal1, chal2))
        bill_chal_no = []
        for chal in chals:
            bill_chal_no.append(chal.challan_no)
        bil.chals = ','.join(bill_chal_no)
    clients = list(client.objects.all().order_by('client_name'))
    return render(request, "bill_get.html", {"bills": bills, "clients": clients})


@login_required
def print_bill(request):
    pdf = bill_pdf(request.POST['bill_no'])
    http = HttpResponse(pdf, content_type='application/pdf')
    http['Content-Disposition'] = 'inline; filename="challan.pdf"'
    return http


@login_required
def add_bill(request):
    clients = list(client.objects.all().order_by('client_name'))
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    dt = dt.split(" ")[0] + "T" + dt.split(" ")[1]
    print(request.body)
    try:
        data = json.loads(request.body)
        dictt = {}
        for i in range(len(data)):
            dictt[list(data[i].items())[0][0]] = list(data[i].items())[0][1]
        table = []
        for i in range(len(dictt['table'])):
            row = {}
            for j in range(len(dictt['table'][i]['value'])):
                row[list(dictt['table'][i]['value'][j].items())[0][0]] = list(dictt['table'][i]['value'][j].items())[0][
                    1]
            table.append(row)
        dictt['table'] = table
        with transaction.atomic():
            clientt = get_object_or_404(client, pk=dictt['client_name'])
            bil_no = bill.objects.all().aggregate(Max('bill_no'))
            if bil_no['bill_no__max']:
                max_bill = bil_no['bill_no__max']
            else:
                max_bill = 0
            bil = bill(bill_no=(max_bill + 1), date=dictt['date'], client_name=clientt,
                       gross_amount=dictt['gross_amount'], other_amount=dictt['other_amount'],
                       total_amount=dictt['total_amount'], gst=dictt['gst'], recieved=0, payment_no=None, deleted=False)
            bil.save()
            try:
                print("bill no ", bil.bill_no)
            except:
                pass
            # challan.delete()
            print(dictt['table'])
            for each in dictt['table']:
                if each['type'] == 'Printout':
                    pchal = get_object_or_404(pchallan, pk=each['challan_no'])
                    pchal.bill_no = bil
                    pchal.save()
                if each['type'] == 'Film':
                    fchal = get_object_or_404(fchallan, pk=each['challan_no'])
                    fchal.bill_no = bil
                    fchal.save()
        print('It was successfully')
        pdf = bill_pdf(bil.bill_no)
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
        try:
            email.send()
        except:
            print("Unable to send the email")
            pass
        http = HttpResponse(pdf, content_type='application/pdf')
        http['Content-Disposition'] = 'inline; filename="challan.pdf"'
        l = logs(user_name=str(request.user),
                 message="Added a bill(Print) for " + str(dictt['client_name']) + " with bill no " + str(
                     bil.bill_no) + ".")
        l.save()
        return http
    except Exception as e:
        print(e)
        raise
        print(e.__class__.__name__)
        if (str(e.__class__.__name__) == 'DataError'):
            return render(request, 'bill_add.html',
                          {"clients": clients, "datetime": dt, 'error_message': "Please provide the data correctly", })
        if (str(e.__class__.__name__) == 'ValidationError'):
            return render(request, 'bill_add.html',
                          {"clients": clients, "datetime": dt, 'error_message': "Please provide the data correctly", })
        else:
            return render(request, 'bill_add.html',
                          {"clients": clients, "datetime": dt, 'error_message': "Some error occured", })


@login_required
def delete_bill(request):
    bills = list(bill.objects.filter(deleted=False).filter(payment_no=None))
    check_user = Employee.objects.get(user=user.objects.get(username=request.user))
    if check_user.role != 'Admin':
        return render(request, 'bill_delete.html',
                      {"bills": bills, 'error_message': "You dont have the permission to modify anything", })
    try:
        with transaction.atomic():
            try:
                selected_choice = bill.objects.get(pk=request.POST['bill_no'])
            except (KeyError, items.DoesNotExist):
                return render(request, 'bill_delete.html',
                              {"bills": bills, 'error_message': "The item group name provided has not been added", })
            selected_choice.deleted = True
            selected_choice.save()
            bills = list(bill.objects.filter(deleted=False).filter(payment_no=None
                                                                   ).order_by('bill_no'))
            chals = pchallan.objects.filter(bill_no=request.POST['bill_no'])
            for chal in chals:
                chal.bill_no = None
                chal.save()
            chals = fchallan.objects.filter(bill_no=request.POST['bill_no'])
            for chal in chals:
                chal.bill_no = None
                chal.save()
            l = logs(user_name=str(request.user), message="Deleted a bill(Film) for " + str(
                selected_choice.client_name.client_name) + " with bill no " + str(request.POST['bill_no']) + ".")
            l.save()
            bills_json = serializers.serialize('json', bills)
            return render(request, "bill_delete.html", {"bills": bills, "bills_json": bills_json,
                                                        'success_message': "Bill deleted successfully"})
    except Exception as e:
        print(e)
        print(e.__class__.__name__)
        if str(e.__class__.__name__) == 'DataError':
            return render(request, 'bill_delete.html',
                          {"bills": bills, 'error_message': "Please provide the data correctly", })
        if str(e.__class__.__name__) == 'ValidationError':
            return render(request, 'bill_delete.html',
                          {"bills": bills, 'error_message': "Please provide the data correctly", })
        else:
            return render(request, 'bill_delete.html', {"bills": bills, 'error_message': "Some error occured", })


from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from num2words import num2words


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
                str(jobs[i].item.item_name)))
        except:
            cnvs.drawString(22 * mm, A4[1] - first - (12 * i),
                            (str(jobs[i].item.item_name) + ', Job- ' + str(jobs[i].job_name)))
        cnvs.drawString(97 * mm, A4[1] - first - (12 * i), jobs[i].item.group_name.hsn_code)
        try:
            cnvs.drawString(112 * mm, A4[1] - first - (12 * i),
                            str(round(jobs[i].width * jobs[i].height * jobs[i].quantity, 2)))
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
