import csv
import json
# Create your views here.
from datetime import datetime

from bill.models import bill
from client.models import client
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User as user
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from fchallan.models import fchallan
from items.models import items
from itertools import chain
from logs.models import logs
from pchallan.models import pchallan
from users.models import Employee
from django.core import serializers

from .models import payment


@login_required
def payment_add(request):
    clients = list(client.objects.all().order_by('client_name'))
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    dt = dt.split(" ")[0] + "T" + dt.split(" ")[1]
    return render(request, "payment_add.html", {"clients": clients, 'datetime': dt})


@login_required
def get_challans(request):
    clients = list(client.objects.all().order_by('client_name'))
    pchallans = list(
        pchallan.objects.filter(client_name=request.POST['client']).filter(bill_no=None).filter(deleted=False).filter(
            payment_no=None))
    fchallans = list(
        fchallan.objects.filter(client_name=request.POST['client']).filter(bill_no=None).filter(deleted=False).filter(
            payment_no=None))
    for each in pchallans:
        each.type = "Printout"
    for each in fchallans:
        each.type = "Film"
    result_list = sorted(chain(pchallans, fchallans), key=lambda instance: instance.date)
    amount = float(request.POST['amount'])
    cl = client.objects.get(client_name=request.POST['client'])
    amount += float(cl.balance)
    summ = 0
    for each in result_list:
        each.checked = False
        each.total_amount = round(each.total_amount, 0)
        summ += each.total_amount
    return render(request, "payment_add.html",
                  {"challans": result_list, "amount_chosen": amount, "datetime_chosen": request.POST['date'],
                   "client_chosen": request.POST['client'], "total_amount": summ, "clients": clients})


@login_required
def add_payment(request):
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
            print(dictt['table'])
            for j in range(len(dictt['table'][i]['value'])):
                row[list(dictt['table'][i]['value'][j].items())[0][0]] = list(dictt['table'][i]['value'][j].items())[0][
                    1]
            table.append(row)
        dictt['table'] = table
        with transaction.atomic():
            clientt = get_object_or_404(client, pk=dictt['client_name'])
            pay = payment(date=dictt['date'], client_name=clientt,
                          remaining_payment=float(dictt['remaining_payment']) - float(clientt.balance))
            pay.save()
            clientt.balance = dictt['remaining_payment']
            clientt.save()
            summ_of_challans = 0
            for each in dictt['table']:
                if (each['type'] == 'Printout'):
                    pchal = get_object_or_404(pchallan, pk=each['challan_no'])
                    pchal.recieved = pchal.total_amount
                    summ_of_challans += pchal.total_amount
                    pchal.payment_no = pay
                    pchal.save()
                if (each['type'] == 'Film'):
                    fchal = get_object_or_404(fchallan, pk=each['challan_no'])
                    fchal.recieved = fchal.total_amount
                    summ_of_challans += fchal.total_amount
                    fchal.payment_no = pay
                    fchal.save()
        l = logs(user_name=str(request.user),
                 message="Added a challan payment for " + str(dictt['client_name']) + " of rs. " + str(
                     float(pay.remaining_payment) + float(summ_of_challans)) + " and payment no" + str(
                     pay.payment_no) + ".")
        l.save()
        return render(request, 'payment_add.html', {"clients": clients, "datetime": dt,
                                                    'success_message': "Payment no " + str(
                                                        pay.payment_no) + " saved successfully", })
    except Exception as e:
        print(e)
        raise
        print(e.__class__.__name__)
        if (str(e.__class__.__name__) == 'DataError'):
            return render(request, 'payment_add.html',
                          {"clients": clients, "datetime": dt, 'error_message': "Please provide the data correctly", })
        if (str(e.__class__.__name__) == 'ValidationError'):
            return render(request, 'payment_add.html',
                          {"clients": clients, "datetime": dt, 'error_message': "Please provide the data correctly", })
        else:
            return render(request, 'payment_add.html',
                          {"clients": clients, "datetime": dt, 'error_message': "Some error occured", })


@login_required
def payment_delete(request):
    payments = list(payment.objects.all())
    payments_json = serializers.serialize('json', payments)
    return render(request, "payment_delete.html", {"payments": payments, "payments_json": payments_json})


@login_required
def payment_print(request):
    payments = list(payment.objects.all())
    return render(request, "payment_print.html", {"payments": payments})


@login_required
def print_payment(request):
    pay = payment.objects.filter(payment_no=request.POST['payment'])[0]
    pchal = pchallan.objects.filter(payment_no=request.POST['payment'])
    fchal = fchallan.objects.filter(payment_no=request.POST['payment'])
    bills = bill.objects.filter(payment_no=request.POST['payment'])
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="somefilename.csv"'
    writer = csv.writer(response)
    t_amount = 0
    for each in list(chain(pchal, fchal, bills)):
        t_amount += each.total_amount
    print(t_amount)
    print(t_amount + pay.remaining_payment)
    writer.writerow(
        ['Challan/Bill', 'Challan/Bill No.', 'Total Amount', 'Date: ' + pay.date.strftime("%Y-%m-%d %H:%M:%S"),
         'Party Name: ' + pay.client_name.client_name, 'Payment No.: ' + str(pay.payment_no),
         'Payment Amount' + str(t_amount + pay.remaining_payment)])
    for each in pchal:
        writer.writerow(['Print Challan', str(each.challan_no), str(each.total_amount), '', '', '', ''])
    for each in fchal:
        writer.writerow(['Film Challan', str(each.challan_no), str(each.total_amount), '', '', '', ''])
    for each in bills:
        writer.writerow(['Bill', str(each.bill_no), str(each.total_amount), '', '', '', ''])
    return response


@login_required
def delete_payment(request):
    payments = list(payment.objects.all())
    check_user = Employee.objects.get(user=user.objects.get(username=request.user))
    if (check_user.role != 'Admin'):
        return render(request, 'payment_delete.html',
                      {"payments": payments, 'error_message': "You dont have the permission to modify anything", })
    try:
        with transaction.atomic():
            chals = pchallan.objects.filter(payment_no=request.POST['payment'])
            for chal in chals:
                chal.payment_no = None
                chal.recieved = 0
                chal.save()
            chals = fchallan.objects.filter(payment_no=request.POST['payment'])
            for chal in chals:
                chal.payment_no = None
                chal.recieved = 0
                chal.save()
            bills = bill.objects.filter(payment_no=request.POST['payment'])
            for bil in bills:
                bil.payment_no = None
                bil.recieved = 0
                bil.save()
            try:
                selected_choice = payment.objects.get(pk=request.POST['payment'])
            except (KeyError, items.DoesNotExist):
                return render(request, 'payment_delete.html', {"payments": payments,
                                                               'error_message': "The item group name provided has not been added", })
            clientt = selected_choice.client_name
            clientt.balance = clientt.balance - selected_choice.remaining_payment
            clientt.save()
            selected_choice.delete()
            payments = list(payment.objects.all())
            l = logs(user_name=str(request.user),
                     message="Delete a payment for " + str(clientt.client_name) + " and payment no" + str(
                         request.POST['payment']) + ".")
            l.save()
            return render(request, 'payment_delete.html',
                          {"payments": payments, 'success_message': "Item Group deleted successfully", })
    except Exception as e:
        raise
        print(e)
        print(e.__class__.__name__)
        if (str(e.__class__.__name__) == 'DataError'):
            return render(request, 'payment_delete.html',
                          {"payments": payments, 'error_message': "Please provide the data correctly", })
        if (str(e.__class__.__name__) == 'ValidationError'):
            return render(request, 'payment_delete.html',
                          {"payments": payments, 'error_message': "Please provide the data correctly", })
        else:
            return render(request, 'payment_delete.html',
                          {"payments": payments, 'error_message': "Some error occured", })

@login_required
def payment_display(request):
    payments = list(payment.objects.order_by('payment_no'))
    for pay in payments:
        chal1 = fchallan.objects.filter(payment_no=pay.payment_no).filter(bill_no__isnull = True)
        chal2 = pchallan.objects.filter(payment_no=pay.payment_no).filter(bill_no__isnull = True)
        bills = bill.objects.filter(payment_no=pay.payment_no)
        for chal in chal1:
            chal.challan_no = str(chal.challan_no) + ' - F'
        for chal in chal2:
            chal.challan_no = str(chal.challan_no) + ' - P'
        for bil in bills:
            bil.bill_no = str(bil.bill_no) + ' - B'
        chals = list(chain(chal1, chal2))
        bill_chal_no = []
        for chal in chals:
            bill_chal_no.append(chal.challan_no)
        for bil in bills:
            bill_chal_no.append(bil.bill_no)
        pay.effected = ', '.join(bill_chal_no)
        chal_pay1 = pchallan.objects.filter(payment_no=pay.payment_no).filter(bill_no__isnull=True)
        chal_pay2 = fchallan.objects.filter(payment_no=pay.payment_no).filter(bill_no__isnull=True)
        bill_pay = bill.objects.filter(payment_no=pay.payment_no)
        chal_pay = list(chain(chal_pay1, chal_pay2, bill_pay))
        amount_sum = 0
        for chal in chal_pay:
            amount_sum += chal.total_amount
        amount_sum = amount_sum + pay.remaining_payment
        pay.tamount = amount_sum
    clients = list(client.objects.all().order_by('client_name'))
    return render(request, "payment_get.html", {"payments": payments, "clients": clients})

@login_required
def filter_date(request):
    payments = list(
        payment.objects.filter(date__range=(request.POST['from'], request.POST['to'])).order_by(
            'payment_no'))
    for pay in payments:
        chal1 = fchallan.objects.filter(payment_no=pay.payment_no).filter(bill_no__isnull = True)
        chal2 = pchallan.objects.filter(payment_no=pay.payment_no).filter(bill_no__isnull = True)
        bills = bill.objects.filter(payment_no=pay.payment_no)
        for chal in chal1:
            chal.challan_no = str(chal.challan_no) + ' - F'
        for chal in chal2:
            chal.challan_no = str(chal.challan_no) + ' - P'
        for bil in bills:
            bil.bill_no = str(bil.bill_no) + ' - B'
        chals = list(chain(chal1, chal2))
        bill_chal_no = []
        for chal in chals:
            bill_chal_no.append(chal.challan_no)
        for bil in bills:
            bill_chal_no.append(bil.bill_no)
        pay.effected = ', '.join(bill_chal_no)
        chal_pay1 = pchallan.objects.filter(payment_no=pay.payment_no).filter(bill_no__isnull=True)
        chal_pay2 = fchallan.objects.filter(payment_no=pay.payment_no).filter(bill_no__isnull=True)
        bill_pay = bill.objects.filter(payment_no=pay.payment_no)
        chal_pay = list(chain(chal_pay1, chal_pay2, bill_pay))
        amount_sum = 0
        for chal in chal_pay:
            amount_sum += chal.total_amount
        amount_sum = amount_sum + pay.remaining_payment
        pay.tamount = amount_sum
    clients = list(client.objects.all().order_by('client_name'))
    return render(request, "payment_get.html", {"payments": payments, "clients": clients})

@login_required
def filter_client(request):
    payments = list(payment.objects.filter(client_name=request.POST['client_name']).order_by('payment_no'))
    for pay in payments:
        chal1 = fchallan.objects.filter(payment_no=pay.payment_no).filter(bill_no__isnull = True)
        chal2 = pchallan.objects.filter(payment_no=pay.payment_no).filter(bill_no__isnull = True)
        bills = bill.objects.filter(payment_no=pay.payment_no)
        for chal in chal1:
            chal.challan_no = str(chal.challan_no) + ' - F'
        for chal in chal2:
            chal.challan_no = str(chal.challan_no) + ' - P'
        for bil in bills:
            bil.bill_no = str(bil.bill_no) + ' - B'
        chals = list(chain(chal1, chal2))
        bill_chal_no = []
        for chal in chals:
            bill_chal_no.append(chal.challan_no)
        for bil in bills:
            bill_chal_no.append(bil.bill_no)
        pay.effected = ', '.join(bill_chal_no)
        chal_pay1 = pchallan.objects.filter(payment_no=pay.payment_no).filter(bill_no__isnull=True)
        chal_pay2 = fchallan.objects.filter(payment_no=pay.payment_no).filter(bill_no__isnull=True)
        bill_pay = bill.objects.filter(payment_no=pay.payment_no)
        chal_pay = list(chain(chal_pay1, chal_pay2, bill_pay))
        amount_sum = 0
        for chal in chal_pay:
            amount_sum += chal.total_amount
        amount_sum = amount_sum + pay.remaining_payment
        pay.tamount = amount_sum
    clients = list(client.objects.all().order_by('client_name'))
    return render(request, "payment_get.html", {"payments": payments, "clients": clients})

@login_required
def payment_add_bill(request):
    clients = list(client.objects.all().order_by('client_name'))
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    dt = dt.split(" ")[0] + "T" + dt.split(" ")[1]
    return render(request, "payment_add_bill.html", {"clients": clients, 'datetime': dt})


@login_required
def get_challans_bill(request):
    clients = list(client.objects.all().order_by('client_name'))
    bills = list(bill.objects.filter(client_name=request.POST['client']).filter(deleted=False).filter(payment_no=None))
    banks = payment.objects.filter(client_name=request.POST['client'])
    banks = [each.bank_name for each in banks]
    banks = list(set(banks))
    result_list = sorted(bills, key=lambda instance: instance.date)
    amount = float(request.POST['amount'])
    cl = client.objects.get(client_name=request.POST['client'])
    amount += float(cl.balance)
    summ = 0
    for each in result_list:
        each.checked = False
        each.total_amount = round(each.total_amount, 0)
        summ += each.total_amount
    return render(request, "payment_add_bill.html",
                  {"banks": banks, "total_amount": summ, "bills": result_list, "amount_chosen": amount,
                   "datetime_chosen": request.POST['date'], "client_chosen": request.POST['client'],
                   "clients": clients})


@login_required
def add_payment_bill(request):
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
            print(dictt['table'])
            for j in range(len(dictt['table'][i]['value'])):
                row[list(dictt['table'][i]['value'][j].items())[0][0]] = list(dictt['table'][i]['value'][j].items())[0][
                    1]
            table.append(row)
        dictt['table'] = table
        if (not (dictt['check_no'] == '' and dictt['bank_name'] == '' and dictt['check_date'] == '')):
            pays = payment.objects.filter(client_name=dictt['client_name'])
            pays = [each.check_no for each in pays]
            if (dictt['check_no'] in pays):
                return render(request, 'payment_add_bill.html', {"clients": clients, "datetime": dt,
                                                                 'error_message': "Check no provided is matching with an old check no", })
        with transaction.atomic():
            clientt = get_object_or_404(client, pk=dictt['client_name'])
            if (dictt['check_no'] == '' and dictt['bank_name'] == '' and dictt['check_date'] == ''):
                pay = payment(date=dictt['date'], client_name=clientt,
                              remaining_payment=float(dictt['remaining_payment']) - float(clientt.balance),
                              pay_type='CASH', check_no=None, bank_name=None, check_date=None)
            else:
                pay = payment(date=dictt['date'], client_name=clientt,
                              remaining_payment=float(dictt['remaining_payment']) - float(clientt.balance),
                              pay_type='CHECK', check_no=dictt['check_no'], bank_name=dictt['bank_name'],
                              check_date=dictt['check_date'])
            pay.save()
            clientt.balance = dictt['remaining_payment']
            clientt.save()
            try:
                print("bill no ", pay.payment_no)
            except:
                pass
            # challan.delete()
            summ = 0
            for each in dictt['table']:
                bil = get_object_or_404(bill, pk=each['bill_no'])
                bil.recieved = bil.total_amount
                bil.payment_no = pay
                bil.save()
                pchals = pchallan.objects.filter(bill_no=bil.bill_no)
                for pchal in pchals:
                    pchal.recieved = pchal.total_amount
                    summ += pchal.total_amount
                    pchal.payment_no = pay
                    pchal.save()
                fchals = fchallan.objects.filter(bill_no=bil.bill_no)
                for fchal in fchals:
                    fchal.recieved = fchal.total_amount
                    summ += fchal.total_amount
                    fchal.payment_no = pay
                    fchal.save()
        print('It was successfully')
        l = logs(user_name=str(request.user),
                 message="Added a bill payment for " + str(dictt['client_name']) + " of rs. " + str(
                     float(pay.remaining_payment) + float(summ)) + " and payment no" + str(pay.payment_no) + ".")
        l.save()
        return render(request, 'payment_add_bill.html', {"clients": clients, "datetime": dt,
                                                         'success_message': "Payment no " + str(
                                                             pay.payment_no) + " saved successfully", })
    except Exception as e:
        print(e)
        raise
        print(e.__class__.__name__)
        if (str(e.__class__.__name__) == 'DataError'):
            return render(request, 'payment_add_bill.html',
                          {"clients": clients, "datetime": dt, 'error_message': "Please provide the data correctly", })
        if (str(e.__class__.__name__) == 'ValidationError'):
            return render(request, 'payment_add_bill.html',
                          {"clients": clients, "datetime": dt, 'error_message': "Please provide the data correctly", })
        else:
            return render(request, 'payment_add_bill.html',
                          {"clients": clients, "datetime": dt, 'error_message': "Some error occured", })
