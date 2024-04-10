


import telebot
import mysql.connector
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot import types
import time

# MySQL database configuration
db_config = {
    'host': '',
    'database': '',
    'user': '',
    'password': '',
    'port': 
    
}

connected = False


# Establish a connection to the MySQL database
while not connected:
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        conn.commit()   
        print("Connection established and committed successfully!")
        connected = True

    except mysql.connector.Error as error:
        print("Error while connecting to MySQL:", error)
        print("Tring to reconnect .....")
        time.sleep(10)


# Telegram bot token
bot_token = ''

# Initialize the bot
bot = telebot.TeleBot(bot_token)
bot.remove_webhook()


# In chat
chat = types.ReplyKeyboardMarkup(row_width=2)
Exit = types.KeyboardButton("انهاء دردشة")
chat.add(Exit)

# Main minu
Main = types.ReplyKeyboardMarkup(row_width=2)
item1 = types.KeyboardButton("الملف الشخصي")
item2 = types.KeyboardButton("قائمة المستخدمين")
item3 = types.KeyboardButton("بدأ الدردشة")
Main.add(item1, item2, item3)

# Yes or No
YON = types.ReplyKeyboardMarkup(row_width=2)
yes = types.KeyboardButton("قبول")
no = types.KeyboardButton("رفض")
YON.add(Exit)

# Profile
Profile = types.ReplyKeyboardMarkup(row_width=2)
photo = types.KeyboardButton("تحديد صورة")
Bio = types.KeyboardButton("تحديد وصف")
name = types.KeyboardButton("تحديد اسم")
mainp = types.KeyboardButton("القائمة الرئيسية")
Profile.add(photo,Bio,name,mainp)

# Handler for processing incoming messages
@bot.message_handler(content_types=['text', 'voice', 'sticker', 'photo', 'animation', 'video'])
def handle_message(message):

    user_id = message.from_user.id
    timestamp = datetime.now()
    
    # Check if the user's photo_mode and baio_mode are both 0
    select_mode_query = "SELECT photo_mode, baio_mode FROM mode WHERE user_id = %s"
    cursor.execute(select_mode_query, (user_id,))
    modes = cursor.fetchone()
    
    # Check if the user exists in the users table
    check_user_query = "SELECT * FROM users WHERE user_id = %s"
    cursor.execute(check_user_query, (user_id,))
    user = cursor.fetchone()

    if not user:
        try:
            # If user doesn't exist, insert the user into the users table
            insert_user_query = "INSERT INTO users (user_id, first_contact_date) VALUES (%s, %s)"
            insert_user_values = (user_id, timestamp)
            cursor.execute(insert_user_query, insert_user_values)
            conn.commit()
            print("User inserted into users table:", user_id)
        except mysql.connector.IntegrityError as e:
            # If duplicate entry error occurs, ignore it
            if e.errno == 1062:
                print("User already exists:", user_id)


    #if message.text and not message.text.startswith('/'):
        # Handle text messages
        message_text = message.text
  

        # Insert the text message into the database with the timestamp
        insert_query = "INSERT INTO messages (user_id, message, timestamp) VALUES (%s, %s, %s)"
        insert_values = (user_id, message_text, timestamp)
        cursor.execute(insert_query, insert_values)
        conn.commit()

        # Reply to the user
        bot.reply_to(message, "Text message stored successfully!")
        print("Text message stored successfully:", message_text)
            
    if message.text and not message.text.startswith('/'):
        message_text = message.text

        # Check if the user's photo_mode and baio_mode are both 0
        select_mode_query = "SELECT photo_mode, baio_mode FROM mode WHERE user_id = %s"
        cursor.execute(select_mode_query, (user_id,))
        modes = cursor.fetchone()

        # Check if there is an active chat for the sender
        select_current_chat_query = "SELECT current_chat FROM users WHERE user_id = %s"
        cursor.execute(select_current_chat_query, (user_id,))
        current_chat = cursor.fetchone() #Name of the recipient
        
        if current_chat[0] != "":
            # There is an active chat for the sender
            recipient_name = current_chat[0]

            # Check if the recipient exists and has an active chat with the sender
            select_recipient_query = "SELECT user_id FROM users WHERE name = %s "
            cursor.execute(select_recipient_query, (recipient_name,))
            recipient_data = cursor.fetchone() #user_id for recipient

            if recipient_data:
                # Recipient exists and has an active chat with the sender, forward the message
                forward_query = "INSERT INTO messages (user_id, message, timestamp) VALUES (%s, %s, %s)"
                forward_values = (recipient_data[0], message_text, timestamp)
                cursor.execute(forward_query, forward_values)
                conn.commit()

                try:
                    bot.send_message(recipient_data[0], message_text)  # Sending the message to the recipient
                    
                except Exception as e:
                    # Handle the error if message sending fails
                    bot.reply_to(message, "Your message did not send it.")
                
            else:
                # Recipient does not exist or does not have an active chat with the sender
                bot.reply_to(message, "No active chat found with the recipient.")
        elif modes and modes[0] == 0 and modes[1] == 0:
            # No active chat found for the sender
            bot.reply_to(message, "No active chat found.")

    if message and message.text and message.text.startswith('/start') or message.text == "القائمة الرئيسية":
        bot.send_message(message.chat.id, "Choose one of the options:", reply_markup=Main)

    if message and message.text and message.text.startswith('/name') or message.text == "تحديد اسم":
        # Check if there is an active chat for the sender
        select_current_chat_query = "SELECT current_chat FROM users WHERE user_id = %s"
        cursor.execute(select_current_chat_query, (message.from_user.id,))
        current_chat = cursor.fetchone()  # Name of the recipient
        
        if current_chat and current_chat[0]:
            bot.reply_to(message, "يرجى الخروج من الدردشة الحالية أولاً.")
        else:
            bot.reply_to(message, "يرجى ادخال اسم لحسابك على ان لا يتجاوز 10 احرف")
            bot.register_next_step_handler(message, set_name)

    if message and message.text and message.text.startswith('/chat') or message.text == "بدأ الدردشة":
        bot.send_message(message.chat.id,"قم بأدخال اسم الحساب لبدأ محادثة معه")
        bot.register_next_step_handler(message, start_chat)
         
    if message and message.text and message.text.startswith('/exit') or message.text =="انهاء دردشة":
        # استرجاع الاسم الموجود في current_chat للمستخدم الحالي
        select_current_chat_query = "SELECT current_chat FROM users WHERE user_id = %s"
        cursor.execute(select_current_chat_query, (user_id,))
        current_chat = cursor.fetchone()

        if current_chat:
            # استرجاع user_id المقابل للمستخدم الحالي
            select_user_id_query = "SELECT user_id FROM users WHERE name = %s"
            cursor.execute(select_user_id_query, (current_chat[0],))
            user_id_to_chat_with = cursor.fetchone()

            if user_id_to_chat_with:
                # إلغاء الدردشة الحالية لكلا المستخدمين
                update_chat_query = "UPDATE users SET current_chat = NULL WHERE user_id IN (%s, %s)"
                cursor.execute(update_chat_query, (user_id, user_id_to_chat_with[0]))
                conn.commit()

                try:
                    bot.send_message(message.chat.id, "تم انهاء المحادثة", reply_markup=Main)
                    bot.send_message(user_id_to_chat_with[0], "تم انهاء المحادثة", reply_markup=Main)
                    
                except telebot.apihelper.ApiTelegramException as e:
                    # في حال حدوث خطأ أثناء إرسال الرسالة
                    print("Failed to send message:", e)


            else:
                bot.reply_to(message, "User ID not found for current chat user")
        else:
            bot.reply_to(message, "Current chat user not found")

    if message and message.text and message.text.startswith('/users') or message.text =="قائمة المستخدمين":
        # Retrieve all user names from the database
        select_users_query = "SELECT name FROM users"
        cursor.execute(select_users_query)
        user_names = [user[0] for user in cursor.fetchall()]  # Extract names from query result
        # If there are user names, send them in a message
        if user_names:
            names_message = "\n".join(user_names)
            bot.reply_to(message, f"Users:\n{names_message}")
        else:
            bot.reply_to(message, "No users found in the database!")

    if message.voice:
        # Extracting voice message data
        voice_id = message.voice.file_id

        # Check if there is an active chat for the sender
        select_current_chat_query = "SELECT current_chat FROM users WHERE user_id = %s"
        cursor.execute(select_current_chat_query, (user_id,))
        current_chat = cursor.fetchone()  # Name of the recipient
        
        if current_chat and current_chat[0]:
            # There is an active chat for the sender
            recipient_name = current_chat[0]

            # Check if the recipient exists and has an active chat with the sender
            select_recipient_query = "SELECT user_id FROM users WHERE name = %s"
            cursor.execute(select_recipient_query, (recipient_name,))
            recipient_data = cursor.fetchone()  # user_id for recipient

            if recipient_data:
                # Recipient exists and has an active chat with the sender, forward the voice message
                #forward_query = "INSERT INTO voice_messages (user_id, voice_id, timestamp) VALUES (%s, %s, %s)"
                #forward_values = (recipient_data[0], voice_id, timestamp)
                #cursor.execute(forward_query, forward_values)
                #conn.commit()

                try:
                    bot.send_voice(recipient_data[0], voice_id)  # Sending the voice message to the recipient
                    
                except Exception as e:
                    # Handle the error if message sending fails
                    bot.reply_to(message, "Your voice message could not be sent.")
                    
            else:
                # Recipient does not exist or does not have an active chat with the sender
                bot.reply_to(message, "No active chat found with the recipient.")
        else:
            # No active chat found for the sender
            bot.reply_to(message, "No active chat found.")

    if message.sticker:
        # Extracting sticker data
        sticker_id = message.sticker.file_id
        
        # Check if there is an active chat for the sender
        select_current_chat_query = "SELECT current_chat FROM users WHERE user_id = %s"
        cursor.execute(select_current_chat_query, (user_id,))
        current_chat = cursor.fetchone()  # Name of the recipient
        
        if current_chat and current_chat[0]:
            # There is an active chat for the sender
            recipient_name = current_chat[0]

            # Check if the recipient exists and has an active chat with the sender
            select_recipient_query = "SELECT user_id FROM users WHERE name = %s"
            cursor.execute(select_recipient_query, (recipient_name,))
            recipient_data = cursor.fetchone()  # user_id for recipient

            if recipient_data:
                # Recipient exists and has an active chat with the sender, forward the sticker
                # forward_query = "INSERT INTO stickers (user_id, sticker_id, timestamp) VALUES (%s, %s, %s)"
                # forward_values = (recipient_data[0], sticker_id, timestamp)
                # cursor.execute(forward_query, forward_values)
                # conn.commit()

                try:
                    bot.send_sticker(recipient_data[0], sticker_id)  # Sending the sticker to the recipient
                    
                except Exception as e:
                    # Handle the error if message sending fails
                    bot.reply_to(message, "Your sticker could not be sent.")
                    
            else:
                # Recipient does not exist or does not have an active chat with the sender
                bot.reply_to(message, "No active chat found with the recipient.")
        else:
            # No active chat found for the sender
            bot.reply_to(message, "No active chat found.")

    if message.photo:
        # Extracting photo data
        photo_id = message.photo[-1].file_id  # Choosing the last (highest resolution) photo

        # Check if there is an active chat for the sender
        select_current_chat_query = "SELECT current_chat FROM users WHERE user_id = %s"
        cursor.execute(select_current_chat_query, (user_id,))
        current_chat = cursor.fetchone()  # Name of the recipient
        
        if current_chat and current_chat[0]:
            # There is an active chat for the sender
            recipient_name = current_chat[0]

            # Check if the recipient exists and has an active chat with the sender
            select_recipient_query = "SELECT user_id FROM users WHERE name = %s"
            cursor.execute(select_recipient_query, (recipient_name,))
            recipient_data = cursor.fetchone()  # user_id for recipient

            if recipient_data:
                # Recipient exists and has an active chat with the sender, forward the photo
                # forward_query = "INSERT INTO photos (user_id, photo_id, timestamp) VALUES (%s, %s, %s)"
                # forward_values = (recipient_data[0], photo_id, timestamp)
                # cursor.execute(forward_query, forward_values)
                # conn.commit()

                try:
                    bot.send_photo(recipient_data[0], photo_id)  # Sending the photo to the recipient
                    
                except Exception as e:
                    # Handle the error if message sending fails
                    bot.reply_to(message, "Your photo could not be sent.")
                    
            else:
                # Recipient does not exist or does not have an active chat with the sender
                bot.reply_to(message, "No active chat found with the recipient.")
        else:
            # No active chat found for the sender
            bot.reply_to(message, "No active chat found.")

    if message.animation:
        # Extracting animation data
        animation_id = message.animation.file_id

        # Check if there is an active chat for the sender
        select_current_chat_query = "SELECT current_chat FROM users WHERE user_id = %s"
        cursor.execute(select_current_chat_query, (user_id,))
        current_chat = cursor.fetchone()  # Name of the recipient
        
        if current_chat and current_chat[0]:
            # There is an active chat for the sender
            recipient_name = current_chat[0]

            # Check if the recipient exists and has an active chat with the sender
            select_recipient_query = "SELECT user_id FROM users WHERE name = %s"
            cursor.execute(select_recipient_query, (recipient_name,))
            recipient_data = cursor.fetchone()  # user_id for recipient

            if recipient_data:
                # Recipient exists and has an active chat with the sender, forward the animation
                # forward_query = "INSERT INTO animations (user_id, animation_id, timestamp) VALUES (%s, %s, %s)"
                # forward_values = (recipient_data[0], animation_id, timestamp)
                # cursor.execute(forward_query, forward_values)
                # conn.commit()

                try:
                    bot.send_animation(recipient_data[0], animation_id)  # Sending the animation to the recipient
                    
                except Exception as e:
                    # Handle the error if message sending fails
                    bot.reply_to(message, "Your animation could not be sent.")
                    
            else:
                # Recipient does not exist or does not have an active chat with the sender
                bot.reply_to(message, "No active chat found with the recipient.")
        else:
            # No active chat found for the sender
            bot.reply_to(message, "No active chat found.")

    if message.video:
        # Extracting video data
        video_id = message.video.file_id

        # Check if there is an active chat for the sender
        select_current_chat_query = "SELECT current_chat FROM users WHERE user_id = %s"
        cursor.execute(select_current_chat_query, (user_id,))
        current_chat = cursor.fetchone()  # Name of the recipient
        
        if current_chat and current_chat[0]:
            # There is an active chat for the sender
            recipient_name = current_chat[0]

            # Check if the recipient exists and has an active chat with the sender
            select_recipient_query = "SELECT user_id FROM users WHERE name = %s"
            cursor.execute(select_recipient_query, (recipient_name,))
            recipient_data = cursor.fetchone()  # user_id for recipient

            if recipient_data:
                # Recipient exists and has an active chat with the sender, forward the video
                # forward_query = "INSERT INTO videos (user_id, video_id, timestamp) VALUES (%s, %s, %s)"
                # forward_values = (recipient_data[0], video_id, timestamp)
                # cursor.execute(forward_query, forward_values)
                # conn.commit()

                try:
                    bot.send_video(recipient_data[0], video_id)  # Sending the video to the recipient
                    
                except Exception as e:
                    # Handle the error if message sending fails
                    bot.reply_to(message, "Your video could not be sent.")
                    
            else:
                # Recipient does not exist or does not have an active chat with the sender
                bot.reply_to(message, "No active chat found with the recipient.")
        else:
            # No active chat found for the sender
            bot.reply_to(message, "No active chat found.")

    if message.text and message.text.startswith('/setbaio') or message.text =="تحديد وصف":
        # Check if there is an active chat for the sender
        select_current_chat_query = "SELECT current_chat FROM users WHERE user_id = %s"
        cursor.execute(select_current_chat_query, (message.from_user.id,))
        current_chat = cursor.fetchone()  # Name of the recipient
        
        if current_chat and current_chat[0]:
            bot.reply_to(message, "يرجى الخروج من الدردشة الحالية أولاً قبل تعيين وصف ملفك الشخصي.")
        else:
            bot.reply_to(message, "يرجى إدخال وصف لملفك الشخصي (بحد أقصى 250 حرفًا)")
            bot.register_next_step_handler(message, set_baio)
        
    if message.text and not message.text.startswith('/') and  modes[0] == 0 and modes[1] == 1: 
        print("baio mode")
        # Get the user_id of the sender
        user_id = message.from_user.id

        # Check if the user's baio mode is set to 1
        select_baio_mode_query = "SELECT baio_mode FROM mode WHERE user_id = %s"
        cursor.execute(select_baio_mode_query, (user_id,))
        baio_mode = cursor.fetchone()

        if len(message.text) > 250 and baio_mode and baio_mode[0] == 1:
            bot.reply_to(message, "Description is too long. Please enter a description with a maximum of 250 characters.")
            return
        
        if baio_mode and baio_mode[0] == 1:
            # Save the photo_id in the users table
            update_photo_query = "UPDATE users SET baio_Prof = %s WHERE user_id = %s"
            cursor.execute(update_photo_query, (message.text, user_id))
            conn.commit()

            # Confirm to the user that the photo has been saved
            bot.reply_to(message, "Your profile description has been saved successfully.")

            # Update baio_mode to 0
            update_baio_mode_query = "UPDATE mode SET baio_mode = 0 WHERE user_id = %s"
            cursor.execute(update_baio_mode_query, (user_id,))
            conn.commit()
 
    if message.text and message.text.startswith('/setphoto') or message.text == "تحديد صورة":
        bot.send_message(message.chat.id, "يرجى إرسال الصورة.")
        bot.register_next_step_handler(message, set_photo)
        
    if message.text and message.text.startswith('/myprofile') or message.text == "الملف الشخصي":
        
        send_profile(message)

    if message and message.text and message.text.startswith('/profile'):
        Search_profile(message)


# To set a profile description
@bot.message_handler(commands=['setbaio'])
def set_baio(message):

    user_id = message.from_user.id
    baio_Prof = message.text

    if len(baio_Prof) > 250:
        bot.reply_to(message, "عذرًا، الرسالة طويلة جدًا. يجب أن تكون الرسالة أقل من 250 حرفًا.")
        return
    try:
        # تحديث القيمة في قاعدة البيانات
        update_query = "UPDATE users SET baio_Prof = %s WHERE user_id = %s"
        cursor.execute(update_query, (baio_Prof, user_id))
        conn.commit()
        # إرسال رسالة تأكيد للمستخدم
        bot.reply_to(message, "تم تحديث وصف حسابك بنجاح.")
    except mysql.connector.Error as e:
        bot.reply_to(message, "هنالك خطأ لم يتم  تحديث وصف ملفك الشخصي")
        print("Error while updating baio_Prof:", e)

    # Check if the user is already in the mode table
    select_mode_query = "SELECT user_id FROM mode WHERE user_id = %s"
    cursor.execute(select_mode_query, (message.from_user.id,))
    existing_user = cursor.fetchone()

    if not existing_user:
        # If the user is not in the mode table, insert their user_id with baio_mode set to 1
        insert_mode_query = "INSERT INTO mode (user_id,  baio_mode) VALUES (%s, 1)"
        cursor.execute(insert_mode_query, (message.from_user.id,))
        conn.commit()
    else:
        # If the user already exists in the mode table, update their baio_mode to 1
        update_mode_query = "UPDATE mode SET baio_mode = 1 WHERE user_id = %s"
        cursor.execute(update_mode_query, (message.from_user.id,))
        conn.commit()

# To set a photo for profile
@bot.message_handler(commands=['setphoto'])
def set_photo(message):
    user_id = message.chat.id
    photo_id = message.photo[-1].file_id

    # Check if there is an active chat for the sender
    select_current_chat_query = "SELECT current_chat FROM users WHERE user_id = %s"
    cursor.execute(select_current_chat_query, (message.from_user.id,))
    current_chat = cursor.fetchone()  # Name of the recipient
    
    if current_chat and current_chat[0]:
        bot.reply_to(message, "يرجى الخروج من الدردشة الحالية أولاً قبل تعيين صورة ملفك الشخصي.")
    elif message.content_type == 'photo':

        try:
            # تحديث الصورة في قاعدة البيانات
            update_query = "UPDATE users SET Photo_Prof = %s WHERE user_id = %s"
            cursor.execute(update_query, (photo_id, user_id))
            conn.commit()

            # إرسال رسالة تأكيد للمستخدم
            bot.send_message(user_id, "تم حفظ الصورة بنجاح.")
        except mysql.connector.Error as e:
            print("Error while updating Photo_Prof:", e)
    else:
        bot.send_message(user_id, "الرجاء إرسال صورة فقط.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    # Check if the message is a photo
    photo_id = message.photo[-1].file_id

    # Get the user_id of the sender
    user_id = message.from_user.id

    # Check if the user's photo mode is set to 1
    select_photo_mode_query = "SELECT photo_mode FROM mode WHERE user_id = %s"
    cursor.execute(select_photo_mode_query, (user_id,))
    photo_mode = cursor.fetchone()

    if photo_mode and photo_mode[0] == 1:
        # Save the photo_id in the users table
        update_photo_query = "UPDATE users SET Photo_Prof = %s WHERE user_id = %s"
        cursor.execute(update_photo_query, (photo_id, user_id))
        conn.commit()

        # Confirm to the user that the photo has been saved
        bot.reply_to(message, "Your profile photo has been saved successfully.")

        # Update photo_mode to 0
        update_photo_mode_query = "UPDATE mode SET photo_mode = 0 WHERE user_id = %s"
        cursor.execute(update_photo_mode_query, (user_id,))
        conn.commit()

def set_name(message):
    user_id = message.chat.id
    name = message.text
    if len(name) > 10:
        bot.reply_to(message, "عذرًا، يجب أن يكون الاسم أقل من 10 أحرف.")
        return
    try:
        # Update the name in the users table
        update_user_query = "UPDATE users SET name = %s WHERE user_id = %s"
        update_user_values = (name, user_id)
        cursor.execute(update_user_query, update_user_values)
        conn.commit()
        print("User name updated in users table:", name)
        bot.reply_to(message, f"تم تحديث الاسم '{name}' بنجاح!")
    except Exception as e:
        print("Error updating user name:", e)
        bot.reply_to(message, f"خطأ في تحديث الاسم '{name}'!")

def send_profile(message):
    bot.send_message(message.chat.id, "ملفك الشخصي", reply_markup=Profile)
    # استعلام قاعدة البيانات للحصول على صورة الملف الشخصي ووصف الملف الشخصي للمستخدم
    select_profile_query = "SELECT Photo_Prof, baio_Prof FROM users WHERE user_id = %s"
    cursor.execute(select_profile_query, (message.from_user.id,))
    profile_data = cursor.fetchone()
    
    if profile_data:
        photo_id = profile_data[0]
        description = profile_data[1] if profile_data[1] else "No description available."

        # استخدام الرسائل الجاهزة لإرسال الصورة والوصف
        photo_msg = types.InputMediaPhoto(media=photo_id, caption=description)
        bot.send_media_group(message.chat.id, [photo_msg])
    else:
        bot.reply_to(message, "No profile data found.")

def Search_profile(message):
    try:
        username = message.text.split('/profile ', 1)[1]
    except:
        return
    

    # ابحث عن اسم المستخدم في قاعدة البيانات
    select_user_query = "SELECT * FROM users WHERE name = %s"
    cursor.execute(select_user_query, (username,))
    user_data = cursor.fetchone()
    
    if user_data:
        select_user_query = "SELECT user_id, Photo_Prof, baio_Prof FROM users WHERE name = %s"
        cursor.execute(select_user_query, (username,))
        user_info = cursor.fetchone()
        
        if user_info:
            user_id, photo_prof, baio_prof = user_info
            
            bot.send_photo(message.chat.id, photo_prof, caption=f"الاسم: {username}\nالوصف:\n{baio_prof}")


    else:
            
            bot.reply_to(message, "User not found.")

def get_user_names(message):
    # Retrieve all user names from the database
    select_users_query = "SELECT name FROM users"
    cursor.execute(select_users_query)
    user_names = [user[0] for user in cursor.fetchall()]  # Extract names from query result
    # If there are user names, send them in a message
    if user_names:
        names_message = "\n".join(user_names)
        bot.reply_to(message, f"Users:\n{names_message}")
    else:
        bot.reply_to(message, "No users found in the database!")

def start_chat(message):

    user_id = message.from_user.id
    name = message.text
   
    # Search for the name in the users table
    select_user_query = "SELECT user_id FROM users WHERE name = %s"
    cursor.execute(select_user_query, (name,))
    user_data = cursor.fetchone()

    # Search for the name of the requester in the users table
    select_user_query = "SELECT name FROM users WHERE user_id = %s"
    cursor.execute(select_user_query, (user_id,))
    name_rquester = cursor.fetchone()

    if user_data and name_rquester != name :
        # Found the user, start a chat
        user_id_to_chat_with = user_data[0]
        bot.send_message(user_id_to_chat_with, f"لديك طلب للمحادثة من {name} ", reply_markup=YON)
        bot.send_message(message.chat.id, f"تم ارسالة طلب محادثة الى {name} بأنتظار الموافقة ")
        
        # Get current user's name
        select_current_user_query = "SELECT name FROM users WHERE user_id = %s"
        cursor.execute(select_current_user_query, (user_id,))
        current_user_name = cursor.fetchone()[0]

        # Insert chat info into the users table for both users
        update_chat_query = "UPDATE users SET current_chat = %s WHERE name = %s"
        chat_values = (name, current_user_name)
        cursor.execute(update_chat_query, chat_values)

        update_chat_query = "UPDATE users SET current_chat = %s WHERE name = %s"
        chat_values = (current_user_name, name)
        cursor.execute(update_chat_query, chat_values)

        conn.commit()

        try:
            
            bot.send_message(message.chat.id, f"محادثة مع {name} بدأت!", reply_markup=chat)
            bot.send_message(user_id_to_chat_with, f"محادثة مع {current_user_name} بدأت!",reply_markup=chat)
        except telebot.apihelper.ApiTelegramException as e:
            # في حال حدوث خطأ أثناء إرسال الرسالة
            print("Failed to send message:", e)

    elif name_rquester == name:
         bot.reply_to(message, "لايمكنك بدأ محادثه مع نفسك.")

    else:
        # User not found
        try:
            bot.reply_to(message, f"المستخدم '{name}' لم يتم العثور عليه!")
        except telebot.apihelper.ApiTelegramException as e:
            # في حالة فشل إرسال الرسالة
            print("Failed to send message:", e)



# Start the bot
            
bot.polling()
