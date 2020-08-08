# Create your views here.
import csv
from datetime import date
from datetime import datetime
from io import BytesIO

import pandas as pd
from client.models import client
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from fchallan.models import fchallan, fjob
from itertools import chain
from payment.models import payment
from pchallan.models import pchallan, pjob
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


@login_required
def report_page(request):
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    dt = dt.split(" ")[0] + "T" + dt.split(" ")[1]
    clients = list(client.objects.all().order_by('client_name'))
    return render(request, "reports.html", {"datetime": datetime, "clients": clients})


@login_required
def b2b_report_get(request):
    challans = bill.objects.filter(deleted=False).filter(date__range=(request.POST['from'], request.POST['to']))
    challans = sorted(challans, key=lambda instance: instance.bill_no)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="b2b.csv"'
    writer = csv.writer(response)
    writer.writerow(['GSTIN/UIN of Recipient', 'Receiver Name', 'Invoice Number', 'Invoice date', 'Invoice Value',
                     'Place Of Supply', 'Reverse Charge', 'Invoice Type', 'E-Commerce GSTIN', 'Rate',
                     'Applicable % of Tax Rate', 'Taxable Value', 'Cess Amount'])
    for bil in challans:
        if (bil.client_name.client_name != 'Cash' and len(bil.client_name.gstin) > 9):
            challansp = pchallan.objects.filter(bill_no=bil.bill_no)
            challansf = fchallan.objects.filter(bill_no=bil.bill_no)
            jobs = []
            for each in challansp:
                jobs.extend(pjob.objects.filter(challan_no=each.challan_no))
            for each in challansf:
                jobs.extend(fjob.objects.filter(challan_no=each.challan_no))
            jobs = sorted(jobs, key=lambda instance: instance.job_date)
            job_dictionary = {}
            for job in jobs:
                if (job.item.group_name.tax in job_dictionary.keys()):
                    job_dictionary[job.item.group_name.tax] += job.amount
                else:
                    job_dictionary[job.item.group_name.tax] = job.amount
            for key, value in job_dictionary.items():
                writer.writerow(
                    [bil.client_name.gstin, bil.client_name.client_name, bil.bill_no, bil.date.strftime("%d-%b-%Y"),
                     round(bil.total_amount, 2), "-".join(bil.client_name.state.split("-")[::-1]), 'N', 'Regular', '',
                     key, '', round(value, 2), ''])
    return response


@login_required
def b2c_report_get(request):
    challans = bill.objects.filter(deleted=False).filter(date__range=(request.POST['from'], request.POST['to']))
    challans = sorted(challans, key=lambda instance: instance.bill_no)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="b2c.csv"'
    writer = csv.writer(response)
    writer.writerow(['Type', 'Place Of Supply', 'Rate', 'Applicable % of Tax Rate', 'Taxable Value', 'Cess Amount',
                     'E-Commerce GSTIN'])
    job_dictionary = {}
    for bil in challans:
        if (bil.client_name.client_name == 'Cash' or len(bil.client_name.gstin) < 9):
            challansp = pchallan.objects.filter(bill_no=bil.bill_no)
            challansf = fchallan.objects.filter(bill_no=bil.bill_no)
            jobs = []
            for each in challansp:
                jobs.extend(pjob.objects.filter(challan_no=each.challan_no))
            for each in challansf:
                jobs.extend(fjob.objects.filter(challan_no=each.challan_no))
            jobs = sorted(jobs, key=lambda instance: instance.job_date)
            for job in jobs:
                if (bil.client_name.state in job_dictionary.keys()):
                    if (job.item.group_name.tax in job_dictionary[bil.client_name.state].keys()):
                        job_dictionary[bil.client_name.state][job.item.group_name.tax] += job.amount
                    else:
                        job_dictionary[bil.client_name.state][job.item.group_name.tax] = job.amount
                else:
                    job_dictionary[bil.client_name.state] = {job.item.group_name.tax: job.amount}
    print(job_dictionary)
    for key, value in job_dictionary.items():
        for key1, value1 in value.items():
            writer.writerow(['OE', "-".join(key.split("-")[::-1]), key1, '', value1, '0.0', ''])
    return response


@login_required
def hsn_report_get(request):
    bills = bill.objects.filter(deleted=False).filter(date__range=(request.POST['from'], request.POST['to']))
    bills = sorted(bills, key=lambda instance: instance.bill_no)
    items = []
    for i in range(len(bills)):
        chal1 = pchallan.objects.filter(deleted=False).filter(bill_no=bills[i].bill_no)
        for each in chal1:
            pjobs = pjob.objects.filter(challan_no=each.challan_no)
            for job in pjobs:
                if ('delhi' in each.client_name.state.lower()):
                    items.append(
                        {"item": job.item, "quantity": int(job.quantity), "amount": float(job.amount + job.gst),
                         "taxable_amount": float(job.amount), "igst": 0.0, "cgst": float(round(job.gst / 2, 2)),
                         "sgst": float(round(job.gst / 2, 2)), "unit": job.unit})
                else:
                    items.append(
                        {"item": job.item, "quantity": int(job.quantity), "amount": float(job.amount + job.gst),
                         "taxable_amount": float(job.amount), "igst": float(round(job.gst, 2)), "cgst": 0.0,
                         "sgst": 0.0, "unit": job.unit})
        chal2 = fchallan.objects.filter(deleted=False).filter(bill_no=bills[i].bill_no)
        for each in chal2:
            fjobs = fjob.objects.filter(challan_no=each.challan_no)
            for job in fjobs:
                if ('delhi' in each.client_name.state.lower()):
                    if (str(job.item.group_name.hsn_code) == "3707"):
                        items.append({"item": job.item, "quantity": float(job.width * job.height * job.quantity),
                                      "amount": float(job.amount + job.gst), "taxable_amount": float(job.amount),
                                      "igst": 0.0, "cgst": float(round(job.gst / 2, 2)),
                                      "sgst": float(round(job.gst / 2, 2)), "unit": job.unit})
                    else:
                        items.append(
                            {"item": job.item, "quantity": int(job.quantity), "amount": float(job.amount + job.gst),
                             "taxable_amount": float(job.amount), "igst": 0.0, "cgst": float(round(job.gst / 2, 2)),
                             "sgst": float(round(job.gst / 2, 2)), "unit": job.unit})
                else:
                    if (str(job.item.group_name.hsn_code) == "3707"):
                        items.append({"item": job.item, "quantity": float(job.width * job.height * job.quantity),
                                      "amount": float(job.amount + job.gst), "taxable_amount": float(job.amount),
                                      "igst": 0.0, "cgst": float(round(job.gst / 2, 2)),
                                      "sgst": float(round(job.gst / 2, 2)), "unit": job.unit})
                    else:
                        items.append(
                            {"item": job.item, "quantity": int(job.quantity), "amount": float(job.amount + job.gst),
                             "taxable_amount": float(job.amount), "igst": float(round(job.gst, 2)), "cgst": 0.0,
                             "sgst": 0.0, "unit": job.unit})
    final_output = {}
    for item in items:
        if (item["item"].group_name in final_output.keys()):
            final_output[item["item"].group_name]["taxable_amount"] += item["taxable_amount"]
            final_output[item["item"].group_name]["igst"] += item["igst"]
            final_output[item["item"].group_name]["sgst"] += item["sgst"]
            final_output[item["item"].group_name]["cgst"] += item["cgst"]
            final_output[item["item"].group_name]["amount"] += item["amount"]
            final_output[item["item"].group_name]["quantity"] += item["quantity"]
        else:
            final_output[item["item"].group_name] = item
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="hsn.csv"'
    writer = csv.writer(response)
    writer.writerow(
        ['HSN', 'Description', 'UQC', 'Total Quantity', 'Total Value', 'Taxable Value', 'Integrated Tax Amount',
         'Central Tax Amount', 'State/UT Tax Amount', 'Cess Amount'])
    units_change_dictionary = {"Inches": "OTH-OTHERS", "Sheets": "PCS-PIECES", "Pieces": "PCS-PIECES"}
    for row in final_output.values():
        writer.writerow([row["item"].group_name.hsn_code, row["item"].group_name.item_group_name,
                         units_change_dictionary[row["item"].unit], row["quantity"], row["amount"],
                         row["taxable_amount"], row["igst"], row["cgst"], row["sgst"], 0.0])
    return response


@login_required
def party_challan_ledger_get(request):
    clientt = client.objects.filter(client_name=request.POST['client_name'])
    chal1 = pchallan.objects.filter(deleted=False).filter(client_name=request.POST['client_name']).filter(
        date__range=(request.POST['from'], request.POST['to'])).filter(bill_no__isnull=True)
    chal2 = fchallan.objects.filter(deleted=False).filter(client_name=request.POST['client_name']).filter(
        date__range=(request.POST['from'], request.POST['to'])).filter(bill_no__isnull=True)
    for ch in chal1:
        ch.new_challan_no = str(ch.challan_no) + '-Print'
    for ch in chal2:
        ch.new_challan_no = str(ch.challan_no) + '-Film'
    pay = payment.objects.filter(client_name=request.POST['client_name']).filter(
        date__range=(request.POST['from'], request.POST['to'])).order_by('date')
    chals = list(chain(chal1, chal2))
    remaining_pay = 0
    for each in pay:
        remaining_pay += each.remaining_payment
    opening_balance = clientt[0].balance - remaining_pay
    chal1_lt_date = pchallan.objects.filter(deleted=False).filter(client_name=request.POST['client_name']).filter(
        date__lt=request.POST['from'])
    chal2_lt_date = fchallan.objects.filter(deleted=False).filter(client_name=request.POST['client_name']).filter(
        date__lt=request.POST['from'])
    chal_lt_date = list(chain(chal1_lt_date, chal2_lt_date))
    sum_balance = 0
    for each in chal_lt_date:
        if (each.payment_no and each.payment_no in payment.objects.filter(
                client_name=request.POST['client_name']).filter(date__lt=request.POST['from'])):
            sum_balance += (float(each.total_amount) - float(each.recieved))
        else:
            sum_balance += (float(each.total_amount) - 0.0)
    a = []
    for each in chals:
        if 'Print' in each.new_challan_no:
            temp_pjobs = pjob.objects.filter(challan_no=int(each.new_challan_no.split("-")[0]))
            slips = [str(temp_pjob.slip_no) for temp_pjob in temp_pjobs]
            slips = list(set(slips))
            slip = "Slip {0}".format(', '.join(slips))
        else:
            slip = "Slip"
        a.append(
            {"date": each.date, "account": slip, "Trans ID": str(each.new_challan_no), "Type": "Slip", "Credit": "",
             "Debit": each.total_amount, "Debit_wo_tax": each.gross_amount, "Total_wo_tax": 0, "Total": "", "Client Balance": ""})
    for each in pay:
        chal_pay1 = pchallan.objects.filter(payment_no=each.payment_no).filter(bill_no__isnull = True)
        chal_pay2 = fchallan.objects.filter(payment_no=each.payment_no).filter(bill_no__isnull = True)
        chal_pay = list(chain(chal_pay1, chal_pay2))
        amount_sum = 0
        for chal in chal_pay:
            amount_sum += chal.total_amount
        amount_sum = amount_sum + each.remaining_payment
        a.append({"date": each.date, "account": "Payment", "Trans ID": str(each.payment_no), "Type": "Slip",
                  "Credit": amount_sum, "Debit": "","Debit_wo_tax": 0, "Total_wo_tax": 0, "Total": "", "Client Balance": ""})
    a = sorted(a, key=lambda x: x["date"])
    a.insert(0,
             {"date": datetime.strptime(request.POST['from'], "%Y-%m-%d"), "account": "Opening Balance", "Trans ID": "",
              "Type": "", "Credit": 0, "Debit": sum_balance, "Debit_wo_tax": 0, "Total_wo_tax": 0, "Total": sum_balance,
              "Client Balance": str(opening_balance)})
    for i in range(1, len(a)):
        if (a[i]['Debit'] == ''):
            a[i]['Debit'] = 0
        if (a[i]['Credit'] == ''):
            a[i]['Credit'] = 0
        if (a[i]['Debit_wo_tax'] == ''):
            a[i]['Debit_wo_tax'] = 0
        a[i]['Total'] = float(a[i - 1]['Total']) + float(a[i]['Debit']) - float(a[i]['Credit'])
        a[i]['Total_wo_tax'] = float(a[i - 1]['Total_wo_tax']) + float(a[i]['Debit_wo_tax']) - float(a[i]['Credit'])
    buffer = BytesIO()
    cnvs = canvas.Canvas(buffer, pagesize=A4)
    cnvs.setLineWidth(.6)
    from math import ceil
    adder = 0
    summ = [0.0, 0.0, 0.0, 0.0]
    cnvs.setFont('Helvetica', 10)
    cnvs.drawString(160 * mm, A4[1] - 105, 'Opening Balance = ' + str(a[0]['Debit']))
    cnvs.drawString(15 * mm, A4[1] - 105, 'From ' + datetime.strptime(request.POST['from'], "%Y-%m-%d").strftime(
        '%d/%m/%Y') + " To " + datetime.strptime(request.POST['to'], "%Y-%m-%d").strftime('%d/%m/%Y'))
    for k in range(ceil(len(a) / 50.0)):
        cnvs.setFont('Helvetica', 12)
        cnvs.translate(mm, mm)
        cnvs.rect(10 * mm, 10 * mm, 190 * mm, 247 * mm, stroke=1, fill=0)
        cnvs.setFont('Helvetica-Bold', 14)
        cnvs.drawString((A4[0] - stringWidth('PK SCAN GRAPHICS', 'Helvetica-Bold', 14)) / 2, A4[1] - 40,
                        'PK SCAN GRAPHICS')
        cnvs.setFont('Helvetica-Bold', 12)
        cnvs.drawString(
            (A4[0] - stringWidth('Client Ledger - ' + request.POST['client_name'], 'Helvetica-Bold', 12)) / 2,
            A4[1] - 60, 'Client Ledger - ' + request.POST['client_name'])
        cnvs.setFont('Helvetica', 8)
        cnvs.line(165 * mm, A4[1] - 114, 165 * mm, A4[1] - 813)
        cnvs.line(140 * mm, A4[1] - 114, 140 * mm, A4[1] - 813)
        cnvs.line(115 * mm, A4[1] - 114, 115 * mm, A4[1] - 813)
        cnvs.line(90 * mm, A4[1] - 114, 90 * mm, A4[1] - 813)
        cnvs.line(65 * mm, A4[1] - 114, 65 * mm, A4[1] - 813)
        cnvs.line(35 * mm, A4[1] - 114, 35 * mm, A4[1] - 813)
        cnvs.drawString(13 * mm, A4[1] - 126, 'Date')
        cnvs.drawString(38 * mm, A4[1] - 126, 'Type')
        cnvs.drawString(68 * mm, A4[1] - 126, 'Slip No')
        cnvs.drawString(93 * mm, A4[1] - 126, 'Credit')
        cnvs.drawString(118 * mm, A4[1] - 126, 'Debit')
        cnvs.drawString(143 * mm, A4[1] - 126, 'Total')
        cnvs.drawString(168 * mm, A4[1] - 126, 'Debit WO Tax')
        first = 143
        for i in range(50 * adder, 50 * (adder + 1)):
            try:
                cnvs.drawString(13 * mm, A4[1] - first - (i - 50 * adder) * 13, a[i + 1]['date'].strftime('%d/%m/%Y'))
                cnvs.setFont('Helvetica', 6)
                cnvs.drawString(38 * mm, A4[1] - first - (i - 50 * adder) * 13, a[i + 1]['account'])
                cnvs.setFont('Helvetica', 8)
                cnvs.drawString(68 * mm, A4[1] - first - (i - 50 * adder) * 13, str(a[i + 1]['Trans ID']))
                cnvs.drawString(93 * mm, A4[1] - first - (i - 50 * adder) * 13, str(round(a[i + 1]['Credit'], 2)))
                cnvs.drawString(118 * mm, A4[1] - first - (i - 50 * adder) * 13, str(round(a[i + 1]['Debit'], 2)))
                cnvs.drawString(143 * mm, A4[1] - first - (i - 50 * adder) * 13, str(round(a[i + 1]['Total'], 2)))
                cnvs.drawString(168 * mm, A4[1] - first - (i - 50 * adder) * 13, str(round(a[i + 1]['Total_wo_tax'], 2)))
                summ[0] += round(float(a[i + 1]['Credit']), 2)
                summ[1] += round(float(a[i + 1]['Debit']), 2)
                summ[2] += round(float(a[i + 1]['Total']), 2)
                summ[3] += round(float(a[i + 1]['Debit_wo_tax']), 2)
            except:
                break
        if (k == (ceil(len(a) / 50.0) - 1)):
            cnvs.setFont('Helvetica-Bold', 10)
            cnvs.line(10 * mm, A4[1] - first - (i - 50 * adder) * 13, 200 * mm, A4[1] - first - (i - 50 * adder) * 13)
            cnvs.drawString(13 * mm, A4[1] - first - (i + 1 - 50 * adder) * 13, "Total")
            cnvs.drawString(38 * mm, A4[1] - first - (i + 1 - 50 * adder) * 13, "")
            cnvs.drawString(68 * mm, A4[1] - first - (i + 1 - 50 * adder) * 13, "")
            cnvs.drawString(93 * mm, A4[1] - first - (i + 1 - 50 * adder) * 13, str(round(summ[0], 2)))
            cnvs.drawString(118 * mm, A4[1] - first - (i + 1 - 50 * adder) * 13, str(round(summ[1], 2)))
            cnvs.drawString(143 * mm, A4[1] - first - (i + 1 - 50 * adder) * 13,
                            str(int(summ[1] - summ[0] + float(a[0]['Debit']))))
            cnvs.drawString(168 * mm, A4[1] - first - (i + 1 - 50 * adder) * 13,
                            str(int(summ[3] - summ[0] + float(a[0]['Debit']))))
            cnvs.line(10 * mm, A4[1] - first - (i + 2 - 50 * adder) * 13, 200 * mm,
                      A4[1] - first - (i + 2 - 50 * adder) * 13)
        adder += 1
        cnvs.showPage()
    cnvs.save()
    pdf = buffer.getvalue()
    buffer.close()
    http = HttpResponse(pdf, content_type='application/pdf')
    http['Content-Disposition'] = 'attachment; filename="challan.pdf"'
    return http

@login_required
def party_combined_ledger_get(request):
    clientt = client.objects.filter(client_name=request.POST['client_name'])
    chal1 = pchallan.objects.filter(deleted=False).filter(client_name=request.POST['client_name']).filter(
        date__range=(request.POST['from'], request.POST['to'])).filter(bill_no__isnull=True)
    chal2 = fchallan.objects.filter(deleted=False).filter(client_name=request.POST['client_name']).filter(
        date__range=(request.POST['from'], request.POST['to'])).filter(bill_no__isnull=True)
    bill1 = bill.objects.filter(deleted=False).filter(client_name=request.POST['client_name']).filter(
        date__range=(request.POST['from'], request.POST['to']))
    for ch in chal1:
        ch.new_challan_no = str(ch.challan_no) + '-Print'
    for ch in chal2:
        ch.new_challan_no = str(ch.challan_no) + '-Film'
    for ch in bill1:
        ch.new_challan_no = str(ch.bill_no) + '-Bill'
    pay = payment.objects.filter(client_name=request.POST['client_name']).filter(
        date__range=(request.POST['from'], request.POST['to'])).order_by('date')
    chals = list(chain(chal1, chal2, bill1))
    remaining_pay = 0
    for each in pay:
        remaining_pay += each.remaining_payment
    opening_balance = clientt[0].balance - remaining_pay
    chal1_lt_date = pchallan.objects.filter(deleted=False).filter(client_name=request.POST['client_name']).filter(
        date__lt=request.POST['from'])
    chal2_lt_date = fchallan.objects.filter(deleted=False).filter(client_name=request.POST['client_name']).filter(
        date__lt=request.POST['from'])
    bill_lt_date = bill.objects.filter(deleted=False).filter(client_name=request.POST['client_name']).filter(
        date__lt=request.POST['from'])
    chal_lt_date = list(chain(chal1_lt_date, chal2_lt_date, bill_lt_date))
    sum_balance = 0
    for each in chal_lt_date:
        if (each.payment_no and each.payment_no in payment.objects.filter(
                client_name=request.POST['client_name']).filter(date__lt=request.POST['from'])):
            sum_balance += (float(each.total_amount) - float(each.recieved))
        else:
            sum_balance += (float(each.total_amount) - 0.0)
    a = []
    for each in chals:
        if 'Print' in each.new_challan_no:
            temp_pjobs = pjob.objects.filter(challan_no=int(each.new_challan_no.split("-")[0]))
            slips = [str(temp_pjob.slip_no) for temp_pjob in temp_pjobs]
            slips = list(set(slips))
            slip = "Slip {0}".format(', '.join(slips))
        elif 'Bill' in each.new_challan_no:
            slip = "Bill"
        else:
            slip = "Slip"
        a.append(
            {"date": each.date, "account": slip, "Trans ID": str(each.new_challan_no), "Type": "Slip", "Credit": "",
             "Debit": each.total_amount, "Debit_wo_tax": each.gross_amount, "Total_wo_tax": 0, "Total": "", "Client Balance": ""})
    for each in pay:
        chal_pay1 = pchallan.objects.filter(payment_no=each.payment_no).filter(bill_no__isnull = True)
        chal_pay2 = fchallan.objects.filter(payment_no=each.payment_no).filter(bill_no__isnull = True)
        bill_pay = bill.objects.filter(payment_no=each.payment_no)
        chal_pay = list(chain(chal_pay1, chal_pay2, bill_pay))
        amount_sum = 0
        for chal in chal_pay:
            amount_sum += chal.total_amount
        amount_sum = amount_sum + each.remaining_payment
        a.append({"date": each.date, "account": "Payment", "Trans ID": str(each.payment_no), "Type": "Slip",
                  "Credit": amount_sum, "Debit": "","Debit_wo_tax": 0, "Total_wo_tax": 0, "Total": "", "Client Balance": ""})
    a = sorted(a, key=lambda x: x["date"])
    a.insert(0,
             {"date": datetime.strptime(request.POST['from'], "%Y-%m-%d"), "account": "Opening Balance", "Trans ID": "",
              "Type": "", "Credit": 0, "Debit": sum_balance, "Debit_wo_tax": 0, "Total_wo_tax": 0, "Total": sum_balance,
              "Client Balance": str(opening_balance)})
    for i in range(1, len(a)):
        if (a[i]['Debit'] == ''):
            a[i]['Debit'] = 0
        if (a[i]['Credit'] == ''):
            a[i]['Credit'] = 0
        if (a[i]['Debit_wo_tax'] == ''):
            a[i]['Debit_wo_tax'] = 0
        a[i]['Total'] = float(a[i - 1]['Total']) + float(a[i]['Debit']) - float(a[i]['Credit'])
        a[i]['Total_wo_tax'] = float(a[i - 1]['Total_wo_tax']) + float(a[i]['Debit_wo_tax']) - float(a[i]['Credit'])
    buffer = BytesIO()
    cnvs = canvas.Canvas(buffer, pagesize=A4)
    cnvs.setLineWidth(.6)
    from math import ceil
    adder = 0
    summ = [0.0, 0.0, 0.0, 0.0]
    cnvs.setFont('Helvetica', 10)
    cnvs.drawString(160 * mm, A4[1] - 105, 'Opening Balance = ' + str(a[0]['Debit']))
    cnvs.drawString(15 * mm, A4[1] - 105, 'From ' + datetime.strptime(request.POST['from'], "%Y-%m-%d").strftime(
        '%d/%m/%Y') + " To " + datetime.strptime(request.POST['to'], "%Y-%m-%d").strftime('%d/%m/%Y'))
    for k in range(ceil(len(a) / 50.0)):
        cnvs.setFont('Helvetica', 12)
        cnvs.translate(mm, mm)
        cnvs.rect(10 * mm, 10 * mm, 190 * mm, 247 * mm, stroke=1, fill=0)
        cnvs.setFont('Helvetica-Bold', 14)
        cnvs.drawString((A4[0] - stringWidth('PK SCAN GRAPHICS', 'Helvetica-Bold', 14)) / 2, A4[1] - 40,
                        'PK SCAN GRAPHICS')
        cnvs.setFont('Helvetica-Bold', 12)
        cnvs.drawString(
            (A4[0] - stringWidth('Client Ledger - ' + request.POST['client_name'], 'Helvetica-Bold', 12)) / 2,
            A4[1] - 60, 'Client Ledger - ' + request.POST['client_name'])
        cnvs.setFont('Helvetica', 8)
        #cnvs.line(165 * mm, A4[1] - 114, 165 * mm, A4[1] - 813)
        cnvs.line(140 * mm, A4[1] - 114, 140 * mm, A4[1] - 813)
        cnvs.line(115 * mm, A4[1] - 114, 115 * mm, A4[1] - 813)
        cnvs.line(90 * mm, A4[1] - 114, 90 * mm, A4[1] - 813)
        cnvs.line(65 * mm, A4[1] - 114, 65 * mm, A4[1] - 813)
        cnvs.line(35 * mm, A4[1] - 114, 35 * mm, A4[1] - 813)
        cnvs.drawString(13 * mm, A4[1] - 126, 'Date')
        cnvs.drawString(38 * mm, A4[1] - 126, 'Type')
        cnvs.drawString(68 * mm, A4[1] - 126, 'Slip No')
        cnvs.drawString(93 * mm, A4[1] - 126, 'Credit')
        cnvs.drawString(118 * mm, A4[1] - 126, 'Debit')
        cnvs.drawString(143 * mm, A4[1] - 126, 'Total')
        #cnvs.drawString(168 * mm, A4[1] - 126, 'Debit WO Tax')
        first = 143
        for i in range(50 * adder, 50 * (adder + 1)):
            try:
                cnvs.drawString(13 * mm, A4[1] - first - (i - 50 * adder) * 13, a[i + 1]['date'].strftime('%d/%m/%Y'))
                cnvs.setFont('Helvetica', 6)
                cnvs.drawString(38 * mm, A4[1] - first - (i - 50 * adder) * 13, a[i + 1]['account'])
                cnvs.setFont('Helvetica', 8)
                cnvs.drawString(68 * mm, A4[1] - first - (i - 50 * adder) * 13, str(a[i + 1]['Trans ID']))
                cnvs.drawString(93 * mm, A4[1] - first - (i - 50 * adder) * 13, str(round(a[i + 1]['Credit'], 2)))
                cnvs.drawString(118 * mm, A4[1] - first - (i - 50 * adder) * 13, str(round(a[i + 1]['Debit'], 2)))
                cnvs.drawString(143 * mm, A4[1] - first - (i - 50 * adder) * 13, str(round(a[i + 1]['Total'], 2)))
                #cnvs.drawString(168 * mm, A4[1] - first - (i - 50 * adder) * 13, str(round(a[i + 1]['Total_wo_tax'], 2)))
                summ[0] += round(float(a[i + 1]['Credit']), 2)
                summ[1] += round(float(a[i + 1]['Debit']), 2)
                summ[2] += round(float(a[i + 1]['Total']), 2)
                #summ[3] += round(float(a[i + 1]['Debit_wo_tax']), 2)
            except:
                break
        if k == (ceil(len(a) / 50.0) - 1):
            cnvs.setFont('Helvetica-Bold', 10)
            cnvs.line(10 * mm, A4[1] - first - (i - 50 * adder) * 13, 200 * mm, A4[1] - first - (i - 50 * adder) * 13)
            cnvs.drawString(13 * mm, A4[1] - first - (i + 1 - 50 * adder) * 13, "Total")
            cnvs.drawString(38 * mm, A4[1] - first - (i + 1 - 50 * adder) * 13, "")
            cnvs.drawString(68 * mm, A4[1] - first - (i + 1 - 50 * adder) * 13, "")
            cnvs.drawString(93 * mm, A4[1] - first - (i + 1 - 50 * adder) * 13, str(round(summ[0], 2)))
            cnvs.drawString(118 * mm, A4[1] - first - (i + 1 - 50 * adder) * 13, str(round(summ[1], 2)))
            cnvs.drawString(143 * mm, A4[1] - first - (i + 1 - 50 * adder) * 13,
                            str(int(summ[1] - summ[0] + float(a[0]['Debit']))))
            #cnvs.drawString(168 * mm, A4[1] - first - (i + 1 - 50 * adder) * 13,
            #                str(int(summ[3] - summ[0] + float(a[0]['Debit']))))
            cnvs.line(10 * mm, A4[1] - first - (i + 2 - 50 * adder) * 13, 200 * mm,
                      A4[1] - first - (i + 2 - 50 * adder) * 13)
        adder += 1
        cnvs.showPage()
    cnvs.save()
    pdf = buffer.getvalue()
    buffer.close()
    http = HttpResponse(pdf, content_type='application/pdf')
    http['Content-Disposition'] = 'attachment; filename="challan.pdf"'
    return http

@login_required
def party_bill_ledger_get(request):
    clientt = client.objects.filter(client_name=request.POST['client_name'])
    bill1 = bill.objects.filter(deleted=False).filter(client_name=request.POST['client_name']).filter(
        date__range=(request.POST['from'], request.POST['to']))
    pay = payment.objects.filter(client_name=request.POST['client_name']).filter(
        date__range=(request.POST['from'], request.POST['to'])).order_by('date')
    remaining_pay = 0
    for each in pay:
        remaining_pay += each.remaining_payment
    opening_balance = clientt[0].balance - remaining_pay
    bill_lt_date = bill.objects.filter(deleted=False).filter(client_name=request.POST['client_name']).filter(
        date__lt=request.POST['from'])
    sum_balance = 0
    for each in bill_lt_date:
        if (each.payment_no and each.payment_no in payment.objects.filter(
                client_name=request.POST['client_name']).filter(date__lt=request.POST['from'])):
            sum_balance += (float(each.total_amount) - float(each.recieved))
        else:
            sum_balance += (float(each.total_amount) - 0.0)
    a = []
    # a.append({"date":datetime.strptime(request.POST['from'],"%Y-%m-%d"),"account":"Opening Balance","Trans ID":"","Type":"","Credit":"","Debit":str(sum_balance),"Total":str(sum_balance),"Client Balance":str(opening_balance)})
    for each in bill1:
        a.append({"date": each.date, "account": "Sale", "Trans ID": str(each.bill_no), "Type": "Sale", "Credit": "",
                  "Debit": each.total_amount, "Total": "", "Client Balance": ""})
    for each in pay:
        bill_pay = bill.objects.filter(payment_no=each.payment_no)
        amount_sum = 0
        for chal in bill_pay:
            amount_sum += chal.total_amount
        amount_sum = amount_sum + each.remaining_payment
        a.append({"date": each.date, "account": "Payment", "Trans ID": str(each.payment_no), "Type": "Sale",
                  "Credit": amount_sum, "Debit": "", "Total": "", "Client Balance": ""})
    a = sorted(a, key=lambda x: x["date"])
    a.insert(0,
             {"date": datetime.strptime(request.POST['from'], "%Y-%m-%d"), "account": "Opening Balance", "Trans ID": "",
              "Type": "", "Credit": "", "Debit": sum_balance, "Total": sum_balance,
              "Client Balance": str(opening_balance)})
    for i in range(1, len(a)):
        if (a[i]['Debit'] == ''):
            a[i]['Debit'] = 0
        if (a[i]['Credit'] == ''):
            a[i]['Credit'] = 0
        a[i]['Total'] = float(a[i - 1]['Total']) + float(a[i]['Debit']) - float(a[i]['Credit'])
    buffer = BytesIO()
    cnvs = canvas.Canvas(buffer, pagesize=A4)
    cnvs.setLineWidth(.6)
    from math import ceil
    adder = 0
    summ = [0.0, 0.0, 0.0]
    cnvs.setFont('Helvetica', 10)
    cnvs.drawString(160 * mm, A4[1] - 105, 'Opening Balance = ' + str(a[0]['Debit']))
    cnvs.drawString(15 * mm, A4[1] - 105, 'From ' + datetime.strptime(request.POST['from'], "%Y-%m-%d").strftime(
        '%d/%m/%Y') + " To " + datetime.strptime(request.POST['to'], "%Y-%m-%d").strftime('%d/%m/%Y'))
    for k in range(ceil(len(a) / 50.0)):
        cnvs.setFont('Helvetica', 12)
        cnvs.translate(mm, mm)
        cnvs.rect(10 * mm, 10 * mm, 190 * mm, 247 * mm, stroke=1, fill=0)
        cnvs.setFont('Helvetica-Bold', 14)
        cnvs.drawString((A4[0] - stringWidth('PK SCAN GRAPHICS', 'Helvetica-Bold', 14)) / 2, A4[1] - 40,
                        'PK SCAN GRAPHICS')
        cnvs.setFont('Helvetica-Bold', 12)
        cnvs.drawString(
            (A4[0] - stringWidth('Client Ledger - ' + request.POST['client_name'], 'Helvetica-Bold', 12)) / 2,
            A4[1] - 60, 'Client Ledger - ' + request.POST['client_name'])
        cnvs.setFont('Helvetica', 8)
        cnvs.line(175 * mm, A4[1] - 114, 175 * mm, A4[1] - 813)
        cnvs.line(145 * mm, A4[1] - 114, 145 * mm, A4[1] - 813)
        cnvs.line(115 * mm, A4[1] - 114, 115 * mm, A4[1] - 813)
        cnvs.line(85 * mm, A4[1] - 114, 85 * mm, A4[1] - 813)
        cnvs.line(55 * mm, A4[1] - 114, 55 * mm, A4[1] - 813)
        cnvs.drawString(13 * mm, A4[1] - 126, 'Date')
        cnvs.drawString(58 * mm, A4[1] - 126, 'Type')
        cnvs.drawString(88 * mm, A4[1] - 126, 'Bill No')
        cnvs.drawString(118 * mm, A4[1] - 126, 'Credit')
        cnvs.drawString(148 * mm, A4[1] - 126, 'Debit')
        cnvs.drawString(178 * mm, A4[1] - 126, 'Total')
        first = 143
        for i in range(50 * adder, 50 * (adder + 1)):
            try:
                cnvs.drawString(13 * mm, A4[1] - first - (i - 50 * adder) * 13, a[i + 1]['date'].strftime('%d/%m/%Y'))
                cnvs.drawString(58 * mm, A4[1] - first - (i - 50 * adder) * 13, a[i + 1]['account'])
                cnvs.drawString(88 * mm, A4[1] - first - (i - 50 * adder) * 13, str(a[i + 1]['Trans ID']))
                cnvs.drawString(118 * mm, A4[1] - first - (i - 50 * adder) * 13, str(round(a[i + 1]['Credit'], 2)))
                cnvs.drawString(148 * mm, A4[1] - first - (i - 50 * adder) * 13, str(round(a[i + 1]['Debit'], 2)))
                cnvs.drawString(178 * mm, A4[1] - first - (i - 50 * adder) * 13, str(round(a[i + 1]['Total'], 2)))
                summ[0] += round(float(a[i + 1]['Credit']), 2)
                summ[1] += round(float(a[i + 1]['Debit']), 2)
                summ[2] += round(float(a[i + 1]['Total']), 2)
            except:
                break
        if (k == (ceil(len(a) / 50.0) - 1)):
            cnvs.setFont('Helvetica-Bold', 10)
            cnvs.line(10 * mm, A4[1] - first - (i - 50 * adder) * 13, 200 * mm, A4[1] - first - (i - 50 * adder) * 13)
            cnvs.drawString(13 * mm, A4[1] - first - (i + 1 - 50 * adder) * 13, "Total")
            cnvs.drawString(58 * mm, A4[1] - first - (i + 1 - 50 * adder) * 13, "")
            cnvs.drawString(88 * mm, A4[1] - first - (i + 1 - 50 * adder) * 13, "")
            cnvs.drawString(118 * mm, A4[1] - first - (i + 1 - 50 * adder) * 13, str(round(summ[0], 2)))
            cnvs.drawString(148 * mm, A4[1] - first - (i + 1 - 50 * adder) * 13, str(round(summ[1], 2)))
            cnvs.drawString(178 * mm, A4[1] - first - (i + 1 - 50 * adder) * 13,
                            str(int(summ[1] - summ[0] + float(a[0]['Debit']))))
            cnvs.line(10 * mm, A4[1] - first - (i + 2 - 50 * adder) * 13, 200 * mm,
                      A4[1] - first - (i + 2 - 50 * adder) * 13)
        adder += 1
        cnvs.showPage()
    cnvs.save()
    pdf = buffer.getvalue()
    buffer.close()
    http = HttpResponse(pdf, content_type='application/pdf')
    http['Content-Disposition'] = 'attachment; filename="challan.pdf"'
    return http


@login_required
def daily_report_get(request):
    payments = list(payment.objects.filter(date__gte=date.today()))
    pchals = pchallan.objects.filter(deleted=False).filter(bill_no=None).filter(date__gte=date.today())
    fchals = fchallan.objects.filter(deleted=False).filter(bill_no=None).filter(date__gte=date.today())
    chals = list(chain(pchals, fchals))
    final_challans = []
    final_challan_list = []
    for pay in payments:
        final_challans.extend(pchallan.objects.filter(payment_no=pay.payment_no))
        final_challans.extend(fchallan.objects.filter(payment_no=pay.payment_no))
    for chal in chals:
        flag = False
        for challan in final_challans:
            if (chal.challan_no == challan.challan_no):
                flag = True
        if (not flag):
            final_challan_list.append(chal)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="somefilename.csv"'
    writer = csv.writer(response)
    writer.writerow(['Account', 'Trans ID', 'Type', 'Debit', 'Credit'])
    for each in final_challans:
        writer.writerow([each.client_name.client_name, str(each.challan_no), 'slip', str(each.total_amount)])
        writer.writerow(['Job Booking', '', '', '', str(each.total_amount)])
    for each in final_challan_list:
        writer.writerow([each.client_name.client_name, str(each.challan_no), 'slip', str(each.total_amount)])
    return response


@login_required
def daily_report_bill_get(request):
    challan_w_payment = bill.objects.filter(deleted=False).filter(date__gte=date.today()).filter(
        payment_no__isnull=False)
    challans_no_payment = bill.objects.filter(deleted=False).filter(date__gte=date.today()).filter(payment_no=None)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="somefilename.csv"'
    writer = csv.writer(response)
    writer.writerow(['Account', 'Trans ID', 'Type', 'Debit', 'Credit'])
    for each in challan_w_payment:
        writer.writerow([each.client_name.client_name, str(each.bill_no), 'local_sale', str(each.total_amount), ''])
        writer.writerow(['Job Booking', '', '', '', str(each.total_amount)])
    for each in challans_no_payment:
        writer.writerow([each.client_name.client_name, str(each.bill_no), 'slip', str(each.total_amount), ''])
    return response


@login_required
def due_list_fchallan_get(request):
    clients = list(client.objects.all())
    challans = []
    for j in range(len(clients)):
        fchals = fchallan.objects.filter(bill_no=None).filter(client_name=clients[j].client_name).filter(
            deleted=False).filter(date__range=(request.POST['from'], request.POST['to']))
        for i in range(len(fchals)):
            fchals[i].challan_no_modified = str(fchals[i].challan_no) + '-Film'
        chals = fchals
        summ = 0
        chal_len = len(challans)
        for i in range(len(chals)):
            if (chals[i].total_amount > chals[i].recieved):
                summ += chals[i].total_amount
                chals[i].t_amount = '-'
                challans.append(chals[i])
        if (chal_len != len(challans)):
            challans[-1].t_amount = summ
    buffer = BytesIO()
    cnvs = canvas.Canvas(buffer, pagesize=A4)
    cnvs.setLineWidth(.6)
    from math import ceil
    a = 0
    summ = 0
    for k in range(ceil(len(challans) / 50.0)):
        cnvs.setFont('Helvetica', 12)
        cnvs.translate(mm, mm)
        cnvs.rect(10 * mm, 10 * mm, 190 * mm, 247 * mm, stroke=1, fill=0)
        cnvs.setFont('Helvetica-Bold', 14)
        cnvs.drawString((A4[0] - stringWidth('Due List', 'Helvetica-Bold', 14)) / 2, A4[1] - 40, 'Due List')
        cnvs.setFont('Helvetica', 8)
        cnvs.line(175 * mm, A4[1] - 114, 175 * mm, A4[1] - 813)
        cnvs.line(145 * mm, A4[1] - 114, 145 * mm, A4[1] - 813)
        cnvs.line(115 * mm, A4[1] - 114, 115 * mm, A4[1] - 813)
        cnvs.line(85 * mm, A4[1] - 114, 85 * mm, A4[1] - 813)
        cnvs.drawString(13 * mm, A4[1] - 126, 'Client Name')
        cnvs.drawString(88 * mm, A4[1] - 126, 'Challan No')
        cnvs.drawString(118 * mm, A4[1] - 126, 'Amount')
        cnvs.drawString(148 * mm, A4[1] - 126, 'Total Amount')
        cnvs.drawString(178 * mm, A4[1] - 126, 'Date')
        first = 143
        for i in range(50 * a, 50 * (a + 1)):
            try:
                cnvs.drawString(13 * mm, A4[1] - first - (i - 50 * a) * 13,
                                challans[i].client_name.client_name + "--" + str(challans[i].client_name.phone1))
                cnvs.drawString(88 * mm, A4[1] - first - (i - 50 * a) * 13, str(challans[i].challan_no_modified))
                cnvs.drawString(118 * mm, A4[1] - first - (i - 50 * a) * 13, str(challans[i].total_amount))
                cnvs.drawString(148 * mm, A4[1] - first - (i - 50 * a) * 13, str(challans[i].t_amount))
                cnvs.drawString(178 * mm, A4[1] - first - (i - 50 * a) * 13, str(challans[i].date.strftime('%d/%m/%Y')))
                summ += challans[i].total_amount
            except:
                break
        if (k == (ceil(len(challans) / 50.0) - 1)):
            cnvs.setFont('Helvetica-Bold', 10)
            cnvs.drawString(13 * mm, A4[1] - first - (i - 50 * a) * 13, "Total")
            cnvs.drawString(33 * mm, A4[1] - first - (i - 50 * a) * 13, "")
            cnvs.drawString(58 * mm, A4[1] - first - (i - 50 * a) * 13, "")
            cnvs.drawString(105 * mm, A4[1] - first - (i - 50 * a) * 13, "")
            cnvs.drawString(178 * mm, A4[1] - first - (i - 50 * a) * 13, str(round(summ, 2)))
        a += 1
        cnvs.showPage()
    cnvs.save()
    pdf = buffer.getvalue()
    buffer.close()
    http = HttpResponse(pdf, content_type='application/pdf')
    http['Content-Disposition'] = 'inline; filename="challan.pdf"'
    return http


@login_required
def due_list_pchallan_get(request):
    clients = list(client.objects.all())
    challans = []
    for j in range(len(clients)):
        pchals = pchallan.objects.filter(bill_no=None).filter(client_name=clients[j].client_name).filter(
            deleted=False).filter(date__range=(request.POST['from'], request.POST['to']))
        for i in range(len(pchals)):
            pchals[i].challan_no_modified = str(pchals[i].challan_no) + '-Printout'
        chals = pchals
        summ = 0
        chal_len = len(challans)
        for i in range(len(chals)):
            if (chals[i].total_amount > chals[i].recieved):
                summ += chals[i].total_amount
                chals[i].t_amount = '-'
                challans.append(chals[i])
        if (chal_len != len(challans)):
            challans[-1].t_amount = summ
    buffer = BytesIO()
    cnvs = canvas.Canvas(buffer, pagesize=A4)
    cnvs.setLineWidth(.6)
    from math import ceil
    a = 0
    summ = 0
    for k in range(ceil(len(challans) / 50.0)):
        cnvs.setFont('Helvetica', 12)
        cnvs.translate(mm, mm)
        cnvs.rect(10 * mm, 10 * mm, 190 * mm, 247 * mm, stroke=1, fill=0)
        cnvs.setFont('Helvetica-Bold', 14)
        cnvs.drawString((A4[0] - stringWidth('Due List', 'Helvetica-Bold', 14)) / 2, A4[1] - 40, 'Due List')
        cnvs.setFont('Helvetica', 8)
        cnvs.line(175 * mm, A4[1] - 114, 175 * mm, A4[1] - 813)
        cnvs.line(145 * mm, A4[1] - 114, 145 * mm, A4[1] - 813)
        cnvs.line(115 * mm, A4[1] - 114, 115 * mm, A4[1] - 813)
        cnvs.line(85 * mm, A4[1] - 114, 85 * mm, A4[1] - 813)
        cnvs.drawString(13 * mm, A4[1] - 126, 'Client Name')
        cnvs.drawString(88 * mm, A4[1] - 126, 'Challan No')
        cnvs.drawString(118 * mm, A4[1] - 126, 'Amount')
        cnvs.drawString(148 * mm, A4[1] - 126, 'Total Amount')
        cnvs.drawString(178 * mm, A4[1] - 126, 'Date')
        first = 143
        for i in range(50 * a, 50 * (a + 1)):
            try:
                cnvs.drawString(13 * mm, A4[1] - first - (i - 50 * a) * 13,
                                challans[i].client_name.client_name + "--" + str(challans[i].client_name.phone1))
                cnvs.drawString(88 * mm, A4[1] - first - (i - 50 * a) * 13, str(challans[i].challan_no_modified))
                cnvs.drawString(118 * mm, A4[1] - first - (i - 50 * a) * 13, str(challans[i].total_amount))
                cnvs.drawString(148 * mm, A4[1] - first - (i - 50 * a) * 13, str(challans[i].t_amount))
                cnvs.drawString(178 * mm, A4[1] - first - (i - 50 * a) * 13, str(challans[i].date.strftime('%d/%m/%Y')))
                summ += challans[i].total_amount
            except:
                break
        if (k == (ceil(len(challans) / 50.0) - 1)):
            cnvs.setFont('Helvetica-Bold', 10)
            cnvs.drawString(13 * mm, A4[1] - first - (i - 50 * a) * 13, "Total")
            cnvs.drawString(33 * mm, A4[1] - first - (i - 50 * a) * 13, "")
            cnvs.drawString(58 * mm, A4[1] - first - (i - 50 * a) * 13, "")
            cnvs.drawString(105 * mm, A4[1] - first - (i - 50 * a) * 13, "")
            cnvs.drawString(178 * mm, A4[1] - first - (i - 50 * a) * 13, str(round(summ, 2)))
        a += 1
        cnvs.showPage()
    cnvs.save()
    pdf = buffer.getvalue()
    buffer.close()
    http = HttpResponse(pdf, content_type='application/pdf')
    http['Content-Disposition'] = 'inline; filename="challan.pdf"'
    return http
    return render(request, "pchallan_get.html")


@login_required
def due_list_partywise_pchallan_get(request):
    clients = list(client.objects.all())
    challans = []
    for j in range(len(clients)):
        pchals = pchallan.objects.filter(bill_no=None).filter(client_name=clients[j].client_name).filter(
            deleted=False).order_by("date")
        for i in range(len(pchals)):
            pchals[i].challan_no_modified = str(pchals[i].challan_no) + '-Printout'
        chals = pchals
        summ = 0
        chal_len = len(challans)
        for i in range(len(chals)):
            if (chals[i].total_amount > chals[i].recieved):
                summ += chals[i].total_amount
                chals[i].t_amount = '-'
                challans.append(chals[i])
        if (chal_len != len(challans)):
            challans[-1].t_amount = summ
    buffer = BytesIO()
    cnvs = canvas.Canvas(buffer, pagesize=A4)
    cnvs.setLineWidth(.6)
    from math import ceil
    a = 0
    summ = 0
    challans_list = []
    for chal in challans:
        challans_list.append({"name": chal.client_name.client_name + "--" + str(chal.client_name.phone1),
                              "date": chal.date, "amount": chal.total_amount})
    df = pd.DataFrame(challans_list)
    df['date'] = pd.to_datetime(df['date'])
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    df = df.groupby([df['date'].dt.strftime('%b'), df['name']])['amount'].sum().reset_index()
    df['date'] = pd.Categorical(df['date'], categories=months, ordered=True)
    df = df.sort_values(["name", "date"])
    df["amount"] = df["amount"].astype(float)
    challans_list = df.values.tolist()
    t_sum = 0
    party_name = ""
    for k in range(ceil(len(challans_list) / 50.0)):
        cnvs.setFont('Helvetica', 12)
        cnvs.translate(mm, mm)
        cnvs.rect(10 * mm, 10 * mm, 190 * mm, 247 * mm, stroke=1, fill=0)
        cnvs.setFont('Helvetica-Bold', 14)
        cnvs.drawString((A4[0] - stringWidth('Due List', 'Helvetica-Bold', 14)) / 2, A4[1] - 40, 'Due List')
        cnvs.setFont('Helvetica', 8)
        cnvs.line(175 * mm, A4[1] - 114, 175 * mm, A4[1] - 813)
        cnvs.line(145 * mm, A4[1] - 114, 145 * mm, A4[1] - 813)
        cnvs.line(115 * mm, A4[1] - 114, 115 * mm, A4[1] - 813)
        cnvs.line(85 * mm, A4[1] - 114, 85 * mm, A4[1] - 813)
        cnvs.drawString(13 * mm, A4[1] - 126, 'Client Name')
        cnvs.drawString(88 * mm, A4[1] - 126, 'Month')
        cnvs.drawString(118 * mm, A4[1] - 126, 'Amount')
        cnvs.drawString(148 * mm, A4[1] - 126, 'Total Amount')
        first = 143
        for i in range(50 * a, 50 * (a + 1)):
            try:
                cnvs.drawString(13 * mm, A4[1] - first - (i - 50 * a) * 13, challans_list[i][1])
                cnvs.drawString(88 * mm, A4[1] - first - (i - 50 * a) * 13, challans_list[i][0])
                cnvs.drawString(118 * mm, A4[1] - first - (i - 50 * a) * 13, str(challans_list[i][2]))
                if (challans_list[i][1] == party_name):
                    cnvs.drawString(148 * mm, A4[1] - first - (i - 50 * a) * 13,
                                    str(round(challans_list[i][2] + t_sum, 2)))
                    t_sum += challans_list[i][2]
                else:
                    cnvs.drawString(148 * mm, A4[1] - first - (i - 50 * a) * 13, str(round(challans_list[i][2], 2)))
                    t_sum = challans_list[i][2]
                    party_name = challans_list[i][1]
                summ += challans_list[i][2]
            except:
                break
        if (k == (ceil(len(challans_list) / 50.0) - 1)):
            cnvs.setFont('Helvetica-Bold', 10)
            cnvs.drawString(13 * mm, A4[1] - first - (i - 50 * a) * 13, "Total")
            cnvs.drawString(33 * mm, A4[1] - first - (i - 50 * a) * 13, "")
            cnvs.drawString(58 * mm, A4[1] - first - (i - 50 * a) * 13, "")
            cnvs.drawString(105 * mm, A4[1] - first - (i - 50 * a) * 13, "")
            cnvs.drawString(178 * mm, A4[1] - first - (i - 50 * a) * 13, str(round(summ, 2)))
        a += 1
        cnvs.showPage()
    cnvs.save()
    pdf = buffer.getvalue()
    buffer.close()
    http = HttpResponse(pdf, content_type='application/pdf')
    http['Content-Disposition'] = 'inline; filename="challan.pdf"'
    return http
    return render(request, "pchallan_get.html")


@login_required
def due_list_bill_get(request):
    clients = list(client.objects.all())
    challans = []
    for j in range(len(clients)):
        pchals = bill.objects.filter(client_name=clients[j].client_name).filter(deleted=False).filter(
            date__range=(request.POST['from'], request.POST['to']))
        chals = pchals
        summ = 0
        chal_len = len(challans)
        for i in range(len(chals)):
            if (chals[i].total_amount > chals[i].recieved):
                summ += chals[i].total_amount
                chals[i].t_amount = '-'
                challans.append(chals[i])
        if (chal_len != len(challans)):
            challans[-1].t_amount = summ
    buffer = BytesIO()
    cnvs = canvas.Canvas(buffer, pagesize=A4)
    cnvs.setLineWidth(.6)
    from math import ceil
    a = 0
    summ = 0
    for k in range(ceil(len(challans) / 50.0)):
        cnvs.setFont('Helvetica', 12)
        cnvs.translate(mm, mm)
        cnvs.rect(10 * mm, 10 * mm, 190 * mm, 247 * mm, stroke=1, fill=0)
        cnvs.setFont('Helvetica-Bold', 14)
        cnvs.drawString((A4[0] - stringWidth('Due List', 'Helvetica-Bold', 14)) / 2, A4[1] - 40, 'Due List')
        cnvs.setFont('Helvetica', 8)
        cnvs.line(175 * mm, A4[1] - 114, 175 * mm, A4[1] - 813)
        cnvs.line(145 * mm, A4[1] - 114, 145 * mm, A4[1] - 813)
        cnvs.line(115 * mm, A4[1] - 114, 115 * mm, A4[1] - 813)
        cnvs.line(85 * mm, A4[1] - 114, 85 * mm, A4[1] - 813)
        cnvs.drawString(13 * mm, A4[1] - 126, 'Client Name')
        cnvs.drawString(88 * mm, A4[1] - 126, 'Bill No')
        cnvs.drawString(118 * mm, A4[1] - 126, 'Amount')
        cnvs.drawString(148 * mm, A4[1] - 126, 'Total Amount')
        cnvs.drawString(178 * mm, A4[1] - 126, 'Date')
        first = 143
        for i in range(50 * a, 50 * (a + 1)):
            try:
                cnvs.drawString(13 * mm, A4[1] - first - (i - 50 * a) * 13,
                                challans[i].client_name.client_name + "--" + str(challans[i].client_name.phone1))
                cnvs.drawString(88 * mm, A4[1] - first - (i - 50 * a) * 13, str(challans[i].bill_no))
                cnvs.drawString(118 * mm, A4[1] - first - (i - 50 * a) * 13, str(challans[i].total_amount))
                cnvs.drawString(148 * mm, A4[1] - first - (i - 50 * a) * 13, str(challans[i].t_amount))
                cnvs.drawString(178 * mm, A4[1] - first - (i - 50 * a) * 13, str(challans[i].date.strftime('%d/%m/%Y')))
                summ += challans[i].total_amount
            except:
                break
        if (k == (ceil(len(challans) / 50.0) - 1)):
            cnvs.setFont('Helvetica-Bold', 10)
            cnvs.drawString(13 * mm, A4[1] - first - (i - 50 * a) * 13, "Total")
            cnvs.drawString(33 * mm, A4[1] - first - (i - 50 * a) * 13, "")
            cnvs.drawString(58 * mm, A4[1] - first - (i - 50 * a) * 13, "")
            cnvs.drawString(105 * mm, A4[1] - first - (i - 50 * a) * 13, "")
            cnvs.drawString(178 * mm, A4[1] - first - (i - 50 * a) * 13, str(round(summ, 2)))
        a += 1
        cnvs.showPage()
    cnvs.save()
    pdf = buffer.getvalue()
    buffer.close()
    http = HttpResponse(pdf, content_type='application/pdf')
    http['Content-Disposition'] = 'inline; filename="challan.pdf"'
    return http
    return render(request, "pchallan_get.html")


@login_required
def due_list_partywise_bill_get(request):
    clients = list(client.objects.all())
    challans = []
    for j in range(len(clients)):
        pchals = bill.objects.filter(client_name=clients[j].client_name).filter(deleted=False).order_by("date")
        chals = pchals
        summ = 0
        chal_len = len(challans)
        for i in range(len(chals)):
            if (chals[i].total_amount > chals[i].recieved):
                summ += chals[i].total_amount
                chals[i].t_amount = '-'
                challans.append(chals[i])
        if (chal_len != len(challans)):
            challans[-1].t_amount = summ
    buffer = BytesIO()
    cnvs = canvas.Canvas(buffer, pagesize=A4)
    cnvs.setLineWidth(.6)
    from math import ceil
    a = 0
    summ = 0
    challans_list = []
    for chal in challans:
        challans_list.append({"name": chal.client_name.client_name + "--" + str(chal.client_name.phone1),
                              "date": chal.date, "amount": chal.total_amount})
    df = pd.DataFrame(challans_list)
    df['date'] = pd.to_datetime(df['date'])
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    df = df.groupby([df['date'].dt.strftime('%b'), df['name']])['amount'].sum().reset_index()
    df['date'] = pd.Categorical(df['date'], categories=months, ordered=True)
    df = df.sort_values(["name", "date"])
    df["amount"] = df["amount"].astype(float)
    challans_list = df.values.tolist()
    t_sum = 0
    party_name = ""
    for k in range(ceil(len(challans_list) / 50.0)):
        cnvs.setFont('Helvetica', 12)
        cnvs.translate(mm, mm)
        cnvs.rect(10 * mm, 10 * mm, 190 * mm, 247 * mm, stroke=1, fill=0)
        cnvs.setFont('Helvetica-Bold', 14)
        cnvs.drawString((A4[0] - stringWidth('Due List', 'Helvetica-Bold', 14)) / 2, A4[1] - 40, 'Due List')
        cnvs.setFont('Helvetica', 8)
        cnvs.line(175 * mm, A4[1] - 114, 175 * mm, A4[1] - 813)
        cnvs.line(145 * mm, A4[1] - 114, 145 * mm, A4[1] - 813)
        cnvs.line(115 * mm, A4[1] - 114, 115 * mm, A4[1] - 813)
        cnvs.line(85 * mm, A4[1] - 114, 85 * mm, A4[1] - 813)
        cnvs.drawString(13 * mm, A4[1] - 126, 'Client Name')
        cnvs.drawString(88 * mm, A4[1] - 126, 'Month')
        cnvs.drawString(118 * mm, A4[1] - 126, 'Amount')
        cnvs.drawString(148 * mm, A4[1] - 126, 'Total Amount')
        first = 143
        for i in range(50 * a, 50 * (a + 1)):
            try:
                cnvs.drawString(13 * mm, A4[1] - first - (i - 50 * a) * 13, challans_list[i][1])
                cnvs.drawString(88 * mm, A4[1] - first - (i - 50 * a) * 13, challans_list[i][0])
                cnvs.drawString(118 * mm, A4[1] - first - (i - 50 * a) * 13, str(challans_list[i][2]))
                if (challans_list[i][1] == party_name):
                    cnvs.drawString(148 * mm, A4[1] - first - (i - 50 * a) * 13,
                                    str(round(challans_list[i][2] + t_sum, 2)))
                    t_sum += challans_list[i][2]
                else:
                    cnvs.drawString(148 * mm, A4[1] - first - (i - 50 * a) * 13, str(round(challans_list[i][2], 2)))
                    t_sum = challans_list[i][2]
                    party_name = challans_list[i][1]
                summ += challans_list[i][2]
            except:
                break
        if (k == (ceil(len(challans_list) / 50.0) - 1)):
            cnvs.setFont('Helvetica-Bold', 10)
            cnvs.drawString(13 * mm, A4[1] - first - (i - 50 * a) * 13, "Total")
            cnvs.drawString(33 * mm, A4[1] - first - (i - 50 * a) * 13, "")
            cnvs.drawString(58 * mm, A4[1] - first - (i - 50 * a) * 13, "")
            cnvs.drawString(105 * mm, A4[1] - first - (i - 50 * a) * 13, "")
            cnvs.drawString(178 * mm, A4[1] - first - (i - 50 * a) * 13, str(round(summ, 2)))
        a += 1
        cnvs.showPage()
    cnvs.save()
    pdf = buffer.getvalue()
    buffer.close()
    http = HttpResponse(pdf, content_type='application/pdf')
    http['Content-Disposition'] = 'inline; filename="challan.pdf"'
    return http
    return render(request, "pchallan_get.html")


from bill.models import bill


@login_required
def sales_register_get(request):
    challans = bill.objects.filter(deleted=False).filter(date__range=(request.POST['from'], request.POST['to']))
    challans = sorted(challans, key=lambda instance: instance.bill_no)
    buffer = BytesIO()
    cnvs = canvas.Canvas(buffer, pagesize=A4)
    cnvs.setLineWidth(.6)
    from math import ceil
    a = 0
    last_row = ['Total', '', '', 0.0, 0.0, 0.0, 0.0]
    for k in range(ceil(len(challans) / 50.0)):
        cnvs.setFont('Helvetica', 12)
        cnvs.translate(mm, mm)
        cnvs.rect(10 * mm, 10 * mm, 190 * mm, 247 * mm, stroke=1, fill=0)
        cnvs.setFont('Helvetica-Bold', 14)
        cnvs.drawString((A4[0] - stringWidth('Due List', 'Helvetica-Bold', 14)) / 2, A4[1] - 40, 'Sales Register')
        cnvs.setFont('Helvetica', 8)
        cnvs.line(30 * mm, A4[1] - 114, 30 * mm, A4[1] - 813)
        cnvs.line(55 * mm, A4[1] - 114, 55 * mm, A4[1] - 813)
        cnvs.line(100 * mm, A4[1] - 114, 100 * mm, A4[1] - 813)
        cnvs.line(125 * mm, A4[1] - 114, 125 * mm, A4[1] - 813)
        cnvs.line(150 * mm, A4[1] - 114, 150 * mm, A4[1] - 813)
        cnvs.line(175 * mm, A4[1] - 114, 175 * mm, A4[1] - 813)
        cnvs.drawString(13 * mm, A4[1] - 126, 'Bill No')
        cnvs.drawString(33 * mm, A4[1] - 126, 'Date')
        cnvs.drawString(58 * mm, A4[1] - 126, 'Client')
        cnvs.drawString(105 * mm, A4[1] - 126, 'Sale Amount')
        cnvs.drawString(130 * mm, A4[1] - 126, 'CGST')
        cnvs.drawString(155 * mm, A4[1] - 126, 'SGST')
        cnvs.drawString(180 * mm, A4[1] - 126, 'IGST')
        first = 143
        for i in range(50 * a, 50 * (a + 1)):
            try:
                cnvs.drawString(13 * mm, A4[1] - first - (i - 50 * a) * 13, str(challans[i].bill_no))
                cnvs.drawString(33 * mm, A4[1] - first - (i - 50 * a) * 13,
                                str(challans[i].date.strftime('%d/%m/%Y')), )
                cnvs.drawString(58 * mm, A4[1] - first - (i - 50 * a) * 13, str(challans[i].client_name.client_name))
                cnvs.drawString(105 * mm, A4[1] - first - (i - 50 * a) * 13, str(challans[i].gross_amount))
                last_row[3] += float(challans[i].gross_amount)
                if ('delhi' in challans[i].client_name.state.lower()):
                    cnvs.drawString(130 * mm, A4[1] - first - (i - 50 * a) * 13, str(challans[i].gst / 2))
                    last_row[4] += float(challans[i].gst / 2)
                    last_row[5] += float(challans[i].gst / 2)
                    cnvs.drawString(155 * mm, A4[1] - first - (i - 50 * a) * 13, str(challans[i].gst / 2))
                    cnvs.drawString(180 * mm, A4[1] - first - (i - 50 * a) * 13, str(0))
                else:
                    cnvs.drawString(130 * mm, A4[1] - first - (i - 50 * a) * 13, str(0))
                    cnvs.drawString(155 * mm, A4[1] - first - (i - 50 * a) * 13, str(0))
                    last_row[6] += float(challans[i].gst)
                    cnvs.drawString(180 * mm, A4[1] - first - (i - 50 * a) * 13, str(challans[i].gst))
            except:
                break
        if (k == (ceil(len(challans) / 50.0) - 1)):
            cnvs.drawString(13 * mm, A4[1] - first - (i - 50 * a) * 13, str(last_row[0]))
            cnvs.drawString(33 * mm, A4[1] - first - (i - 50 * a) * 13, str(last_row[1]), )
            cnvs.drawString(58 * mm, A4[1] - first - (i - 50 * a) * 13, str(last_row[2]))
            cnvs.drawString(105 * mm, A4[1] - first - (i - 50 * a) * 13, str(round(last_row[3], 2)))
            cnvs.drawString(130 * mm, A4[1] - first - (i - 50 * a) * 13, str(round(last_row[4], 2)))
            cnvs.drawString(155 * mm, A4[1] - first - (i - 50 * a) * 13, str(round(last_row[5], 2)))
            cnvs.drawString(180 * mm, A4[1] - first - (i - 50 * a) * 13, str(round(last_row[6], 2)))
        a += 1
        cnvs.showPage()
    cnvs.save()
    pdf = buffer.getvalue()
    buffer.close()
    http = HttpResponse(pdf, content_type='application/pdf')
    http['Content-Disposition'] = 'inline; filename="challan.pdf"'
    return http
