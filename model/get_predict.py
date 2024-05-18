def get_predictions(title,post,commentaire,saved_model):
    from transformers import DistilBertTokenizer,AutoModelForSequenceClassification
    import torch
    saved_model=torch.load(f"{saved_model}")
    tokenizer=DistilBertTokenizer.from_pretrained("distilbert-base-uncased")
    model =  AutoModelForSequenceClassification.from_pretrained('distilbert-base-uncased',
                                                      problem_type="multi_label_classification", 
                                                      num_labels=3,                  
                                                     )
    model.load_state_dict(state_dict)
    device = torch.device("cpu")
    model.to(device)
    
    model.eval()
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
    print(id2label)
    return id2label[preds.item()]
