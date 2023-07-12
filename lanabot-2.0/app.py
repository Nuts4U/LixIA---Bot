from flask import Flask, render_template,request,redirect,jsonify
import subprocess
import signal
import os
import stripe
from datetime import datetime,timedelta
import json
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)-8s %(message)s',
    filename='admin.log'
)

# Flask APP
app = Flask(__name__)
stripe.api_key ="sk_test_51N1VTwSJhh2ijTXxso3U3P7XoTbne9lebm6vF4yQpAwvCd6J0K5cGvPaxZCMC0hU4socuXDEcLGHWA5CDKnsmHXi002eSQUKEF"
endpoint_secret ="whsec_IRZvZmqCc3bd6U3BMgdpIO6qt6ohOzM1"

cred = credentials.Certificate('firebase_auth.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

subscription_data = {
    "uyevgd_hg34rff_hdhs45_gdg45":"daily",
    "dfghjk_56dcdgh_sfdghcj_sfdgh":"weekly",
    "fdghf78_sfgdhj_67vsdb_tsyd":"monthly",
    "gsgdv_56sfsg_gydu_64gry":"yearly",
    "tsgdgsd_fdgsh34_rwtyer":"topup"
}

@app.route("/")
def index():
    return ("Welcome to lana bot.")

@app.route("/start")
def start():
    global script_process,script_pid
    script_process=subprocess.Popen(["python", "bot.py"])
    script_pid = script_process.pid
    return "Bot started!"

@app.route("/stop")
def stop():
    global script_process,script_pid
    os.kill(script_pid,signal.SIGTERM)
    return "Bot stopped!"


@app.route('/payment/success')
def payment_success():
    return render_template('success.html')

@app.route('/payment/cancel')
def payment_cancel():
    return render_template('cancel.html')


@app.route("/payment")
def payment():
    chat_id = request.args.get('chat_id')
    subs_id = request.args.get('subs_id')

    if subs_id =="dfghjk_56dcdgh_sfdghcj_sfdgh":
        price_id ="price_1N1jtTSJhh2ijTXx7r9gp3n7"
    elif subs_id == "fdghf78_sfgdhj_67vsdb_tsyd":
        price_id ="price_1N1lVESJhh2ijTXx6oNWaFsi"
    elif subs_id =="uyevgd_hg34rff_hdhs45_gdg45":
        price_id ="price_1N2GKjSJhh2ijTXxFTbYIsUQ"
    elif subs_id =="gsgdv_56sfsg_gydu_64gry":
        price_id ="price_1N2GPmSJhh2ijTXxFU3iWKRW"
    elif subs_id =="tsgdgsd_fdgsh34_rwtyer":
        price_id ="price_1N2GQaSJhh2ijTXxVp0XGsbo"
    else: 
        return 'Invalid Subscription ID'
    
    if not price_id =="price_1N2GQaSJhh2ijTXxVp0XGsbo": 
        checkout_session= stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price':price_id,
                'quantity':1,
            },],
            mode='subscription',
            subscription_data={
                'metadata':{'chat_id':chat_id,'subs_id':subs_id},
            },
            success_url=request.url_root + 'payment/success',
            cancel_url= request.url_root + 'payment/cancel'
        )
    elif price_id =="price_1N2GQaSJhh2ijTXxVp0XGsbo":
        checkout_session= stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price':price_id,
                'quantity':1,
            },],
            mode='payment',
            metadata ={
                'chat_id':chat_id,
                'subs_id':subs_id},

            success_url=request.url_root + 'payment/success',
            cancel_url= request.url_root + 'payment/cancel'
        )

    return redirect(checkout_session.url,code=302)

@app.route('/paymentwebhook',methods=['POST'])
def webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        return '', 400
    except stripe.error.SignatureVerificationError as e:
        return '', 400
    
    event_data = event.data
    if event_data['object']['object'] == "payment_intent":
        if event_data['object']['status'] == "succeeded":
            invoice_id =  event_data['object']['invoice']
            if not invoice_id == None:
                try:
                    invoice = stripe.Invoice.retrieve(invoice_id)
                    if invoice.billing_reason =="subscription_create":
                        metadata = invoice.lines.data[0].metadata
                        chat_id= metadata['chat_id']
                        subs_id= metadata['subs_id']
                        add_pro_user(chatID=chat_id,subsID=subs_id)
                except Exception as e:
                    print(f"Error in adding pro member : {e}")

    elif event_data['object']['object'] == "invoice":
        invoice_id =  event_data['object']['id']
        invoice = stripe.Invoice.retrieve(invoice_id)
        if invoice.billing_reason =="subscription_cycle":
            if invoice.paid:
                metadata= invoice.lines.data[0].metadata
                chat_id= metadata['chat_id']
                subs_id= metadata['subs_id']
                add_pro_user(chatID=chat_id,subsID=subs_id)
                
    elif event_data['object']['object'] =="checkout.session":
        if event_data['object']['payment_status'] =="paid":
            if event_data['object']['metadata']:
                try:
                    metadata = event_data['object']['metadata']
                    chat_id= metadata['chat_id']
                    subs_id= metadata['subs_id']
                    add_pro_user(chatID=chat_id,subsID=subs_id)
                except Exception as e:
                    print(f"Error adding topup credits : {e}")
                
    handle_event(event)

    return '', 200

def add_pro_user(chatID,subsID):

    payments_data ={}

    read_db(payments_data,'payments_data')
    if not str(chatID) in payments_data:
        payments_data[str(chatID)] ={}
        payments_data[str(chatID)]['subscription_details'] = {}
        payments_data[str(chatID)]['image_prompts'] =0
        
    selected_plan = subscription_data[subsID]
    if not selected_plan =="topup":
        current_datetime = datetime.now()
        one_day_later = current_datetime+timedelta(days=1)
        one_week_later = current_datetime + timedelta(weeks=1)
        one_month_later = current_datetime.replace(month=current_datetime.month+1)
        one_year_later = current_datetime.replace(year=current_datetime.year+1)
        if selected_plan=="weekly":
            payments_data[str(chatID)]['image_prompts'] =  1
            payments_data[str(chatID)]['subscription_details']['plan'] = selected_plan
            payments_data[str(chatID)]['subscription_details']['expiration_time'] = one_week_later
        elif selected_plan=="monthly":
            payments_data[str(chatID)]['image_prompts'] =  1
            payments_data[str(chatID)]['subscription_details']['plan'] = selected_plan
            payments_data[str(chatID)]['subscription_details']['expiration_time'] = one_month_later
        elif selected_plan =="yearly":
            payments_data[str(chatID)]['image_prompts'] =  1
            payments_data[str(chatID)]['subscription_details']['plan'] = selected_plan
            payments_data[str(chatID)]['subscription_details']['expiration_time'] = one_year_later
        elif selected_plan =="daily":
            payments_data[str(chatID)]['image_prompts'] =  1
            payments_data[str(chatID)]['subscription_details']['plan'] = selected_plan
            payments_data[str(chatID)]['subscription_details']['expiration_time'] = one_day_later

    elif selected_plan =="topup":
            payments_data[str(chatID)]['image_prompts'] = 10

    write_to_db(payments_data,'payments_data')


def write_to_db(dictonary_name,dict_name):
    try:
        for key,value in dictonary_name.items():
            doc_ref = db.collection(dict_name).document(key)
            doc_ref.set(value)

    except Exception as e:
        print(f"Error in exception {e}")

def read_db(wDictonary,dict_name):
    data_ref = db.collection(dict_name)
    data_docs = data_ref.get()
    for doc in data_docs:
        wDictonary[doc.id] = doc.to_dict()

def handle_event(event):
    event_data = json.loads(json.dumps(event.data))
    with open('event_data.json', 'a') as f:
        f.write(json.dumps(event_data) + '\n')

@app.route('/showpayload', methods=['GET'])
def show_payload():
    try:
        with open('event_data.json','r') as f:
            payloads= [json.loads(line) for line in f]

        return jsonify(payloads)
    except Exception as e:
        return("None received")

@app.route('/logs')
def logs():
    if os.path.exists('admin.log'):
        with open ('admin.log','r') as f:
            logs = f.read().strip().split('\n')
        logs.reverse()

        return render_template('logs.html',logs= logs)
    else:
        return("No logs found")


if __name__ == "__main__":
    app.run(debug=False,host='0.0.0.0')