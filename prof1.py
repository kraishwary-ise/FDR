import conf,  json, time, math, statistics,requests
from boltiot import Sms, Email, Bolt
def send_telegram_message(message):
    """Sends message via Telegram"""
    url = "https://api.telegram.org/" + conf.telegram_bot_id + "/sendMessage"
    data = {
        "chat_id": conf.telegram_chat_id,
        "text": message
    }
    try:
        response = requests.request(
            "GET",
            url,
            params=data
        )
        print("This is the Telegram response")
        print(response.text)
        telegram_data = json.loads(response.text)
        return telegram_data["ok"]
    except Exception as e:
        print("An error occurred in sending the alert message via Telegram")
        print(e)
        return False


def compute_bounds(history_data, frame_size, factor):
    if len(history_data) < frame_size:
        return None

    if len(history_data) > frame_size:
        del history_data[0:len(history_data) - frame_size]
    Mn = statistics.mean(history_data)
    Variance = 0
    for data in history_data:
        Variance += math.pow((data - Mn), 2)
    Zn = factor * math.sqrt(Variance / frame_size)
    High_bound = history_data[frame_size - 1] + Zn
    Low_Bound = history_data[frame_size - 1] - Zn
    return [High_bound, Low_Bound]


minimum_limit = 5
maximum_limit = 11

mybolt = Bolt(conf.API_KEY, conf.DEVICE_ID)
mailer = Email(conf.MAILGUN_API_KEY, conf.SANDBOX_URL, conf.SENDER_EMAIL, conf.RECIPIENT_EMAIL)

history_data = []

while True:
    response = mybolt.analogRead('A0')
    data = json.loads(response)

    if data['success'] != '1':
        print("There was an error while retriving the data.")
        print("This is the error:" + data['value'])
        time.sleep(10)
        continue

    print("The sensor value is " + (data['value']))
    sensor_value = 0
    try:
        sensor_value = int(data['value'])


    except Exception as e:
        print("There was an error while parsing the response: ", e)
        continue

    bound = compute_bounds(history_data, conf.FRAME_SIZE, conf.MUL_FACTOR)
    if not bound:
        required_data_count = conf.FRAME_SIZE - len(history_data)
        print("Not enough data to compute Z-score. We Need ", required_data_count, " more data points")
        history_data.append(int(data['value']))
        time.sleep(9)
        continue

    try:
        if sensor_value > maximum_limit or sensor_value < minimum_limit:
            response = mailer.send_email("Alert", "The Current temperature is beyond the threshold ")
            message = "Alert " +  \
                      ". Current temperature of Fridge  Room is " + str(sensor_value) + "Statue:=IRREVALANT"
            telegram_status = send_telegram_message(message)
            print("This is the Telegram  Response", telegram_status)
        if sensor_value > bound[0]:
            print("The temperature increased Within Calculated Threshold . Triggering Alerts on 2 Channel/n1.Email/n2.Telegram")
            response = mailer.send_email("Alert", "The Current temperature is beyond the threshold ch1 SOMEONE OPENED Dppr ")
            message = "Alert The temperature increased Within Calculated Threshold ch2 "  + \
                      ".Someone opened Door Current temperature of Fridge  Room is " + str(sensor_value) + "Statue:=Tel_Sucess"
            telegram_status = send_telegram_message(message)

            print("This is the response ", (response))
            print("This is the Telegram  Response", telegram_status)

        elif sensor_value < bound[1]:
            print("The temperature decended  suddenly. Triggering an email nd Broadcast.")

            response = mailer.send_email("Someone opened Fridge Door  via CH1")
            message = "Alert The temperature increased Within Calculated Threshold ch2 " +  \
                      ". Current temperature of Fridge  Room is " + str(sensor_value) + "Statue:=Tel_Sucess"
            telegram_status = send_telegram_message(message)

            print("This is the response ", (response))
            print("This is the Telegram  Response", telegram_status)

        history_data.append(sensor_value);
    except Exception as e:
        print("Error", e)
    time.sleep(10)