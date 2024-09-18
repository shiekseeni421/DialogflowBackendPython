from flask import Flask, request, jsonify
from flask_cors import CORS
from google.cloud import dialogflow_v2 as dialogflow
from google.protobuf import struct_pb2
import os
import logging


logging.basicConfig(filename="services_info.log", level=logging.INFO)

app = Flask(__name__)
CORS(app)

# Helper function to create a session client


def create_session_client(key_file):
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = key_file
    return dialogflow.SessionsClient()


# Helper function to detect intent
def detect_intent(session_client, project_id, session_id, query, language_code, user_name):
    session_path = session_client.session_path(project_id, session_id)
    text_input = dialogflow.TextInput(text=query, language_code=language_code)
    query_input = dialogflow.QueryInput(text=text_input)

    # Constructing payload using Struct
    payload = struct_pb2.Struct()
    payload['userName'] = user_name
    payload['language'] = language_code
    query_params = dialogflow.QueryParameters(payload=payload)
    request = dialogflow.DetectIntentRequest(
        session=session_path,
        query_input=query_input,
        query_params=query_params
    )
    response = session_client.detect_intent(request=request)
    return (response.query_result)


# API endpoint to handle Dialogflow requests
@app.route('/chatbot', methods=['POST'])
def handle_vikaspedia():
    key_filename = os.path.join(os.path.dirname(
        __file__), 'file.json')
    session_client = create_session_client(key_filename)
    data = request.json
    query = data.get('query')
    session_id = data.get('sessionId')
    language_code = data.get('languageCode')
    user_name = data.get('userName')
    try:
        project_id = "projectid"
        result = detect_intent(session_client, project_id,
                               session_id, query, language_code, user_name)
        fulfillment_messages_dict = []
        if len(result.fulfillment_messages)>0:
            for message in result.fulfillment_messages:
                 if 'text' in message:
                     value = {'type': 'text', 'text': list(message.text.text)}
                     fulfillment_messages_dict.append(value)
                 elif 'payload' in message:
                    Type = dict(message.payload)
                    if 'buttons' in Type:
                        value = {'type': "buttons",'buttons': list(Type['buttons'])}
                        fulfillment_messages_dict.append(value)
                    elif 'list' in Type:
                        listValue = dict(message.payload['list'])
                        value = {'type': "list",'list': list(listValue['text']), 'title': str(listValue['title'])}
                        fulfillment_messages_dict.append(value)
                    elif 'listItems' in Type:
                        listOfObject = []
                        listItems = dict(Type['listItems'])
                        for i in listItems['items']:
                            i = dict(i)
                            newItem = {'contextPath': i['contextPath'], 'content_id': i['content_id'],
                                   'title': i['title'], 'description': i['description']}
                            listOfObject.append(newItem)
                        value = {
                            'type': 'listItems',
                            'listItems': listOfObject,
                        }
                        fulfillment_messages_dict.append(value)
                    elif 'listOfText' in Type:
                        listOfObject = []
                        for i in Type['listOfText']:
                            i = dict(i)
                            newItem = {'list': list(
                            i['text']), 'title': i['title']}
                            listOfObject.append(newItem)
                        value = {
                            'type': 'listOfText',
                            'listOfText': listOfObject,
                            }
                        fulfillment_messages_dict.append(value)
        else:
            value = {'type': 'text', 'text': "Something went wrong. Please try again later."}
            fulfillment_messages_dict.append(value)
        return jsonify({"fulfillmentMessages": fulfillment_messages_dict}), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500


# Start the Flask server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3015)
