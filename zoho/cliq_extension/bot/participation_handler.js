
// 1. Define Backend URL
backend_url = "https://6zr1t9v1-5000.inc1.devtunnels.ms/api/cliq/event";
// 2. Initialize the payload map
event_payload = Map();
// 3. Add basic info (These variables exist directly)
event_payload.put("operation",operation);
event_payload.put("user",user);
// 4. Extract Channel info (Docs say it is called 'chat', not 'channel')
if(chat != null)
{
	event_payload.put("channel_id",chat.get("id"));
}
// 5. CRITICAL FIX: Extract Text from 'data' variable
// We only do this if the operation is 'message_sent'
if(operation == "message_sent")
{
	// The docs say 'message' is inside 'data'
	messageObj = data.get("message");
	if(messageObj != null)
	{
		// Extract the actual text content
		text_content = messageObj.get("text");
		event_payload.put("text",text_content);
	}
}
// 6. Send to Backend
response = invokeurl
[
	url :backend_url
	type :POST
	parameters:event_payload
];
// 7. Return Backend Reply
result = Map();
if(response.containsKey("text"))
{
	result.put("text",response.get("text"));
}
else
{
	// Fallback if backend fails
	result.put("text","Backend received event but returned no text.");
}
return result;
