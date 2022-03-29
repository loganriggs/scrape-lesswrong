import requests, json, pprint

# --header "Content-Type: application/json" \
#   --request POST \
#   --data '{"context":"eleutherai", "top_p": 0.9, "temp": 0.75}

# r = requests.post('http://b55a-35-222-129-15.ngrok.io/complete',
#                     data=json.dumps({"string": 'Discussion Title: Is AI the biggest danger of the 21st century?\n\n- AI is the biggest danger of the 21st century.\n\t-Pro:',
#                                      "max_new_tokens": 250 , "top_p": 0.9, "temp": 0.85 , "num_return_sequences":1}),
#                     headers={"Content-Type": "application/json"})
url = "http://a01e-34-66-77-100.ngrok.io"
r = requests.post(url + '/complete',
                    data=json.dumps({"context":"eleutherai", "top_p": 0.9, "temp": 0.75}),
                    headers={"Content-Type": "application/json"})

#https://api.openai.com/v1/engines/davinci/completions
#sk-6lbxfDY85nRNKinsN3jJAX5gTIKq1f5RhOiIVCo1