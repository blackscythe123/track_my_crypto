
// 1. Define Backend URL (Ensure this is your RENDER URL)
backend_url = "https://track-my-crypto.onrender.com/api/cliq/event";

// 2. Initialize Payload
event_payload = Map();
event_payload.put("operation", operation);
event_payload.put("user", user);

// 3. Add Context (Chat/Channel)
if(chat != null) {
    event_payload.put("channel_id", chat.get("id"));
}

// 4. Add Data (Contains Command args or Message text)
if(data != null) {
    // Flatten data into payload so backend sees 'command', 'text', etc. directly
    event_payload.putAll(data);
    
    // For Message Handler: Extract text explicitly if nested
    if(data.get("message") != null) {
        event_payload.put("text", data.get("message").get("text"));
    }
}

// 5. Send to Backend as JSON (More reliable than form-data)
response = invokeurl
[
    url : backend_url
    type : POST
    parameters : event_payload.toString()
    headers : {"Content-Type": "application/json"}
];

// 6. Return Result
result = Map();
if(response.get("text") != null) {
    result.put("text", response.get("text"));
} else {
    // Debugging: Show what happened if no text returned
    result.put("text", "⚠️ Backend Error: " + response);
}
return result;
