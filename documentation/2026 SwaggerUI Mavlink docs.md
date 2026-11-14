2026 SwaggerUI Mavlink docs

How to use blueos swaggerUI to manually send mavlink messages

If you need to manually send mavlink messages (like STATUSTEXT) for testing purposes so that you don't have to use the actual robot (the robot still has to be on), keep reading:

First of all, a SwaggerUI is basically a REST API tool where you can very easily get and post information from and to endpoints. 

Blueos's SwaggerUI is hosted on port 6040, so navigate to [http\://blueos.local:6040/docs/](http://blueos.local:6040/docs/index.html?url=/docs.json#/default/get_info) (you'll need Blueos up and running to get this page to load).

On this page, you will see a bunch of get and post endpoints. The specific ones that are important to message sending are the get endpoint /v1/helper/mavlink, and the post endpoint /mavlink.

We'll start with the get one. Click on the box and it should expand. Click Try it out in the top right part of the expanded box, and you should be able to type in the name parameter box. Enter the name of the message you want to manually send, and click execute. This will return (hopefully a 200\) with a response of the json format for that message. You will need this, so copy it somewhere.

Now go to the /v1/mavlink post endpoint and expand it. This Swagger page is kinda annoying, and they didnt add parameters for this endpoint, so you have to do it manually. Click the execute button and copy the curl command into a terminal. Replace the \-d ' ' section with the json data from your message with whatever information you want in your message (so you will have \-d '{data}'. That curl command should hopefully run in the terminal without errors, and the message will be sent\!

