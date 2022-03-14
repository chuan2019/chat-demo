#!/bin/bash

# test case: if no analyst online, client login will fail
curl -X POST http://localhost:8080/client/login -c cookies/cookiefile_alex -d '{"nickname":"alex"}' -H "Content-Type: application/json"

# prepare analysts, such that clients can initiate chats
## check:
##   1. in the command line check the response message to see if the analyst is added as expected
##   2. in a redis-cli shell check:
##       a. if the analyst nickname is appended to the `analysts_online` sorted list (with the latest timestamp)
##       b. if this is the first analyst logged in, check if the `current_analyst` with value -1 is added

curl -X POST http://localhost:8080/analyst/login -c cookies/cookiefile_joe   -d '{"nickname":"joe"}'   -H "Content-Type: application/json"
sleep 1
curl -X POST http://localhost:8080/analyst/login -c cookies/cookiefile_steve -d '{"nickname":"steve"}' -H "Content-Type: application/json"
sleep 1
curl -X POST http://localhost:8080/analyst/login -c cookies/cookiefile_bob   -d '{"nickname":"bob"}'   -H "Content-Type: application/json"

# test case: check if picking analyst in a round robin way works
## check:
##   1. in the command line check the response message to see if the room string is correct or not
##   2. in a redis-cli shell check
##       a. if the client name is added into the `clients_online` set
##       b. if the `current_analyst` value is incremented by 1
##       c. if a sorted list with `room:<analyst_nickname>:<client_nickname>` with expected analyst nickname and client nickname is created,
##          and it only contains one single "message": "0"

## room:joe:alex
curl -X POST http://localhost:8080/client/login  -c cookies/cookiefile_alex -d '{"nickname":"alex"}' -H "Content-Type: application/json"
## room:steve:mary
curl -X POST http://localhost:8080/client/login  -c cookies/cookiefile_mary -d '{"nickname":"mary"}' -H "Content-Type: application/json"
## room:bob:jack
curl -X POST http://localhost:8080/client/login  -c cookies/cookiefile_jack -d '{"nickname":"jack"}' -H "Content-Type: application/json"
## room:joe:mike
curl -X POST http://localhost:8080/client/login  -c cookies/cookiefile_mike -d '{"nickname":"mike"}' -H "Content-Type: application/json"
## room:steve:mary closed
curl -X POST http://localhost:8080/client/logout -b cookies/cookiefile_mary
## room:steve:mary
curl -X POST http://localhost:8080/client/login  -c cookies/cookiefile_mary -d '{"nickname":"mary"}' -H "Content-Type: application/json"
## room:steve:mary closed
curl -X POST http://localhost:8080/client/logout -b cookies/cookiefile_mary
## room:bob:mary
curl -X POST http://localhost:8080/client/login  -c cookies/cookiefile_mary -d '{"nickname":"mary"}' -H "Content-Type: application/json"
## room:bob:jack closed
curl -X POST http://localhost:8080/client/logout -b cookies/cookiefile_jack
## room:joe:jack
curl -X POST http://localhost:8080/client/login  -c cookies/cookiefile_jack -d '{"nickname":"jack"}' -H "Content-Type: application/json"


# test case: login with same nickname will fail
curl -X POST http://localhost:8080/client/login -c cookies/cookiefile_mary -d '{"nickname":"mary"}' -H "Content-Type: application/json"

# test case: send messages (one client)
## check:
##   1. in a redis-cli shell subscribe to the room:joe:alex channel to confirm messages are sent as expected
##   2. in another redis-cli shell check the contents in the room:joe:alex sorted list to confirm the messages are added into the list
##   3. using get_messages WebApi to retrieve all the messages from both client side (alex) and analyst side (joe) to confirm the messages are added

## as alex is not in the same room with steve, this request will fail
curl -X POST http://localhost:8080/send_msg -b cookies/cookiefile_steve   -d '{"message":"Hi, alex, how are you?", "to":"alex"}' -H "Content-Type: application/json"

curl -X POST http://localhost:8080/send_msg -b cookies/cookiefile_alex -d '{"message":"hi, joe, how are you?"}' -H "Content-Type: application/json"
sleep 1
curl -X POST http://localhost:8080/send_msg -b cookies/cookiefile_joe  -d '{"message":"I am good, thanks, how are you?", "to":"alex"}' -H "Content-Type: application/json"
sleep 1
curl -X POST http://localhost:8080/send_msg -b cookies/cookiefile_alex -d '{"message":"I am good too. Thank you!"}' -H "Content-Type: application/json"
sleep 1
curl -X POST http://localhost:8080/send_msg -b cookies/cookiefile_joe  -d '{"message":"how can I help you?", "to":"alex"}' -H "Content-Type: application/json"

curl -X GET http://localhost:8080/get_messages -b cookies/cookiefile_alex
curl -X GET http://localhost:8080/get_messages -b cookies/cookiefile_joe


# test case: send messages (multiple clients)
## check:
##   1. in a redis-cli shell subscribe to the room:joe:jack channel to confirm messages are sent as expected
##   2. in another redis-cli shell check the contents in the room:joe:jack sorted list to confirm the messages are added into the list
##   3. using get_messages WebApi to retrieve all the messages from both client side (jack) and analyst side (joe) to confirm the messages are added

sleep 1
curl -X POST http://localhost:8080/send_msg -b cookies/cookiefile_joe  -d '{"message":"Hey Jack!", "to":"jack"}' -H "Content-Type: application/json"
sleep 1
curl -X POST http://localhost:8080/send_msg -b cookies/cookiefile_jack -d '{"message":"Hi, Joe! How are you?"}' -H "Content-Type: application/json"
sleep 1
curl -X POST http://localhost:8080/send_msg -b cookies/cookiefile_joe  -d '{"message":"I am good, thank you! How can I help you today?", "to":"jack"}' -H "Content-Type: application/json"

curl -X GET http://localhost:8080/get_messages -b cookies/cookiefile_jack
curl -X GET http://localhost:8080/get_messages -b cookies/cookiefile_joe


# test case: pop messages (multiple clients)
## check:
##   1. in command line check if all messages are returned as expected
##   2. in a redis-cli shell check if messages are deleted after the pop messages api is called

curl -X GET http://localhost:8080/pop_messages -b cookies/cookiefile_jack
curl -X GET http://localhost:8080/pop_messages -b cookies/cookiefile_joe

# clean up

## as there are still clients in communication, this request will fail
curl -X POST http://localhost:8080/analyst/logout -b cookies/cookiefile_joe

curl -X POST http://localhost:8080/client/logout -b cookies/cookiefile_alex
curl -X POST http://localhost:8080/client/logout -b cookies/cookiefile_mary
curl -X POST http://localhost:8080/client/logout -b cookies/cookiefile_jack
curl -X POST http://localhost:8080/client/logout -b cookies/cookiefile_mike

curl -X POST http://localhost:8080/analyst/logout -b cookies/cookiefile_joe
curl -X POST http://localhost:8080/analyst/logout -b cookies/cookiefile_steve
curl -X POST http://localhost:8080/analyst/logout -b cookies/cookiefile_bob
