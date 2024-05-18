def get_predictions(title,post,commentaire, model, tokenizer):
    id2label={
          0:"neutral",
          1:"with palestine",
          2:"with israel"
    }
    model.eval()
    inputs = tokenizer("title: "+title+"\n"+"post: "+post+"\n"+"comment: "+commentaire, return_tensors="pt", padding=True, truncation=True, max_length=512)
    input_ids = inputs['input_ids'].to(device)
    attention_mask = inputs['attention_mask'].to(device)

    with torch.no_grad():
        outputs = model(input_ids, attention_mask=attention_mask)
        logits = outputs.logits
        _, preds = torch.max(logits, dim=1)
    
    return id2label[preds.item()]