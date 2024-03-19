import json
import urllib.request
import os

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
            for destination in record["ses"]["mail"]["destination"]:
                service = destination.split('@')[0].lower()
                print("Found service", service)
                url = os.environ.get(service + "_target")
                if url is None:
                    notify_discord(os.environ.get("test_target"), "AWS Lambda", "Target url not defined for service", service)
                else:
                    notify_discord(url, m_from, m_subject, "")
        elif record["eventSource"] == "aws:sns":
            sns_contents = json.loads(record["Sns"]["Message"])
            m_subject = sns_contents["mail"]["commonHeaders"]["subject"]
            m_from = sns_contents["mail"]["commonHeaders"]["from"][0] #why tf is this an array
            m_body = sns_contents["content"].split('\n\n')[1]
            
            for destination in sns_contents["mail"]["destination"]:
                service = destination.split('@')[0].lower()
                print("Found service", service)
                url = os.environ.get(service + "_target")
                if url is None:
                    notify_discord(os.environ.get("test_target"), "AWS Lambda", "Target url not defined for service", service)
                else:
                    notify_discord(url, m_from, m_subject, m_body)
        else:
            notify_discord(os.environ.get("test_target"), "AWS Lambda", "Unknown eventSource", record["eventSource"])
            continue
        
    return {
        'statusCode': 200,
        'body': json.dumps(event)
    }
