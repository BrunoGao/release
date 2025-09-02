from bigScreen.bigScreen import send_wechat_alert

# Test data
heart_rate = 140
user_openid = "wx10dcc9f0235e1d77"  # Replace with a valid openid for testing
user_name = "Test User"

# Call the function and print the result
response = send_wechat_alert(heart_rate, user_openid, user_name)
print(response)