import json
import urllib.request
import os

def notify(service, push_from, push_subject, push_body):
    schema = os.environ.get(service + "_schema")
    target = os.environ.get(service + "_target")
    if target is None:
        notify_discord(os.environ.get("test_target"), "AWS Lambda", "Target url not defined for service", service)
    else:
        if schema == "discord":
            notify_discord(target, push_from, push_subject, push_body)
        elif schema == "pushover":
            notify_pushover(target, push_from, push_subject, push_body)
        else:
            notify_discord(os.environ.get("test_target"), "AWS Lambda", "Schema not defined for service", service)

def notify_pushover(user, push_from, push_subject, push_body):
    new_subject = push_from + " - " + push_subject
    if push_body == "":
        push_body = "(no message was provided)"
    data = {
        "token": os.environ.get("config_token_pushover"),
        "user": user,
        "title": new_subject[:250],
        "message": push_body[:1024]
    }
    
    request = urllib.request.Request("https://api.pushover.net/1/messages.json", urllib.parse.urlencode(data).encode("ascii"))
    request.add_header('Content-Type', 'application/x-www-form-urlencoded')
    request.add_header('User-Agent', 'Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11 PixilicSESWebhookLambda/1')
    
    response = urllib.request.urlopen(request)
    print(response.read())
    

def notify_discord(url, push_from, push_subject, push_body):
    #for all params, see https://discordapp.com/developers/docs/resources/webhook#execute-webhook
    data = {
        "username" : push_from
    }

    data["embeds"] = [{
        "description" : push_body,
        "title" : push_subject
    }]

    request = urllib.request.Request(url, json.dumps(data).encode('utf-8'))
    request.add_header('Content-Type', 'application/json')
    request.add_header('User-Agent', 'Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11 PixilicSESWebhookLambda/1')

    response = urllib.request.urlopen(request)
    response.read()

    

def lambda_handler(event, context):
    if not "Records" in event:
        notify_discord(os.environ.get("test_target"), "AWS Lambda", "weird event", json.dumps(event))
    for record in event["Records"]:
        if "eventSource" not in record:
            if "EventSource" in record:
                record["eventSource"] = record["EventSource"] #what the fuck?
            else:
                notify_discord(os.environ.get("test_target"), "AWS Lambda", "No eventSource", json.dumps(record))
                continue
        
        #we forsure have an eventSource
        if record["eventSource"] == "aws:ses":
            m_subject = record["ses"]["mail"]["commonHeaders"]["subject"]
            m_from = record["ses"]["mail"]["commonHeaders"]["from"][0] #why tf is this an array
            #no bodies if we got it via ses directly
            
            for destination in record["ses"]["mail"]["destination"]:
                service = destination.split('@')[0].lower()
                print("ses Found service", service)
                #REAL NOTIFICATION
                notify(service, m_from, m_subject, "")
        elif record["eventSource"] == "aws:sns":
            sns_contents = json.loads(record["Sns"]["Message"])
            m_subject = sns_contents["mail"]["commonHeaders"]["subject"]
            m_from = sns_contents["mail"]["commonHeaders"]["from"][0] #why tf is this an array
            try:
                m_body_list = sns_contents["content"].replace('\r\n','\n').split('\n\n')[1:]
                m_body = '\n\n'.join(m_body_list)
            except IndexError:
                m_body = sns_contents["content"]

            for destination in sns_contents["mail"]["destination"]:
                service = destination.split('@')[0].lower()
                print("sns Found service", service)
                #REAL NOTIFICATION
                notify(service, m_from, m_subject, m_body)
        else:
            notify_discord(os.environ.get("test_target"), "AWS Lambda", "Unknown eventSource", record["eventSource"])
            continue
        
    return {
        'statusCode': 200,
        'body': json.dumps(event)
    }
