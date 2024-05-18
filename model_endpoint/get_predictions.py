from transformers import DistilBertTokenizer, AutoModelForSequenceClassification
import torch
import warnings
import logging
warnings.filterwarnings("ignore")
import flask
from flask import request

logging.basicConfig(level=logging.INFO)

# Load the model
saved_model = "IPCBert.bin"
state_dict = torch.load(f"{saved_model}", map_location=torch.device('cpu'))
tokenizer = DistilBertTokenizer.from_pretrained("distilbert-base-uncased")
model =  AutoModelForSequenceClassification.from_pretrained('distilbert-base-uncased',
                                                    problem_type="multi_label_classification", 
                                                    num_labels=3,                  
                                                    )
model.load_state_dict(state_dict)
# Run the model on the CPU
device = torch.device("cpu")
model.to(device)
model.eval()

# Flask app
app = flask.Flask(__name__)

def get_predictions(title, post, commentaire, model=model, tokenizer=tokenizer, device=device):
    inputs = tokenizer("title of the post: "+title+"\n"+"post: "+post+"\n"+"comment: "+commentaire, return_tensors="pt", padding=True, truncation=True, max_length=512)
    input_ids = inputs['input_ids'].to(device)
    attention_mask = inputs['attention_mask'].to(device)

    with torch.no_grad():
        outputs = model(input_ids, attention_mask=attention_mask)
        logits = outputs.logits
        _, preds = torch.max(logits, dim=1)
    id2label={
          0:"neutral",
          1:"with palestine",
          2:"with israel"
    }
    return id2label[preds.item()]

@app.route('/predict', methods=['POST', 'GET'])
def predict():
    if request.method == 'POST':
        title = request.json['title']
        post = request.json['post']
        comment = request.json['comment']
        logging.info(f"Title: {title}, Post: {post}, Comment: {comment}")
        return get_predictions(title, post, comment)
    else:
        return "Hello, please send a POST request with the title, post and comment."

if __name__ == "__main__":
    app.run(host='localhost', port=5000)