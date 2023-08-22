# Import libraries
import RPi.GPIO as GPIO
import random
import ES2EEPROMUtils
import os
import time
# some global variables that need to change as we run the program
end_of_game = None  # set if the user wins or ends the game
global TScore, Tname
global actual_value
global guess_value

# DEFINE THE PINS USED HERE
LED_value = [11, 13, 15]
LED_accuracy = 32
btn_submit = 16
btn_increase = 18
buzzer = 33
eeprom = ES2EEPROMUtils.ES2EEPROM()


# Print the game banner
def welcome():
    os.system('clear')
    print("  _   _                 _                  _____ _            __  __ _")
    print("| \ | |               | |                / ____| |          / _|/ _| |")
    print("|  \| |_   _ _ __ ___ | |__   ___ _ __  | (___ | |__  _   _| |_| |_| | ___ ")
    print("| . ` | | | | '_ ` _ \| '_ \ / _ \ '__|  \___ \| '_ \| | | |  _|  _| |/ _ \\")
    print("| |\  | |_| | | | | | | |_) |  __/ |     ____) | | | | |_| | | | | | |  __/")
    print("|_| \_|\__,_|_| |_| |_|_.__/ \___|_|    |_____/|_| |_|\__,_|_| |_| |_|\___|")
    print("")
    print("Guess the number and immortalise your name in the High Score Hall of Fame!")


# Print the game menu
def menu():

    global actual_value
    global end_of_game
    option = input("Select an option:   H - View High Scores     P - Play Game       Q - Quit\n")
    option = option.upper()
    if option == "H":
        os.system('clear')
        print("HIGH SCORES!!")
        s_count, ss = fetch_scores()
        display_scores(s_count, ss)
    elif option == "P":
        os.system('clear')
        print("Starting a new round!")
        print("Use the buttons on the Pi to make and submit your guess!")
        print("Press and hold the guess button to cancel your game")
        actual_value = generate_number()
        while not end_of_game:
            pass
    elif option == "Q":
        print("Come back soon!")
        exit()
    else:
        print("Invalid option. Please select a valid one!")

def display_scores(count, raw_data):
    #Display the total number of scores stored on the EEPROM
    l = len(raw_data)
    print("There are {} scores. Here are the top 3!".format(count))
    #If the amount of scores is 3 or more then just display the top 3
    if l >= 3:
       print("1st place: " + raw_data[0][0]+" score: "+str(raw_data[0][1]))
       print("2nd place: " + raw_data[1][0]+" score: "+str(raw_data[1][1]))
       print("3rd place: " + raw_data[2][0]+" score: "+str(raw_data[2][1]))
    #If the amount of scores is just 2 then just display the top 2
    elif l == 2:
       print("1st place: " + raw_data[0][0]+" score: "+str(raw_data[0][1]))
       print("2nd place: " + raw_data[1][0]+" score: "+str(raw_data[1][1]))
    #If the amount of scores is just 1 then just display that score    
    elif l ==1:
       print("1st place: " + raw_data[0][0]+" score: "+str(raw_data[0][1]))
    #If there are no scores then:
    else:
       print("There are no scores to display :(")
    pass

# Setup Pins
def setup():
    global guess_value
    guess_value =0
 
    # Setup board mode
    GPIO.setmode(GPIO.BOARD)

    #setp regular GPIO
    GPIO.setup(LED_value[0], GPIO.OUT)
    GPIO.setup(LED_value[1], GPIO.OUT)
    GPIO.setup(LED_value[2], GPIO.OUT)
    GPIO.setup(LED_accuracy, GPIO.OUT)
    
    GPIO.output(LED_value[0],GPIO.LOW)
    GPIO.output(LED_value[1],GPIO.LOW)
    GPIO.output(LED_value[2],GPIO.LOW)
    
    GPIO.setup(btn_submit, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(btn_increase, GPIO.IN,pull_up_down = GPIO.PUD_UP)

    # Setup PWM channels
    global LED_red
    LED_red = GPIO.PWM(LED_accuracy, 1000)
    
    global Buzzer_pwm
    Buzzer_pwm = GPIO.PWM(buzzer,1)
    Buzzer_pwm.stop()
    GPIO.output(buzzer,GPIO.LOW)
    
    # Setup debouncing and callbacks
    GPIO.add_event_detect(btn_submit, GPIO.FALLING, callback = btn_guess_pressed, bouncetime = 200)
    GPIO.add_event_detect(btn_increase, GPIO.FALLING, callback = btn_increase_pressed, bouncetime = 200)
    pass


# Load high scores
def fetch_scores():

    track_score = 7
    #initialize array scores
    scores = [] 
    #get however many scores there are
    score_count = eeprom.read_byte(0)
   
    #for loop to iterate through the registers
    for i in range(0,score_count):
        name = ""
        #Get the parts of the persons name and append them in a string 
        for k in range((i+1)*4,(i+1)*4+3):
            name = name + chr(eeprom.read_byte(k))
        #Get all the scores and add them to an array    
        scores.append([name,eeprom.read_byte(track_score)])
        #Move to the next register and begin the for loop again
        track_score+=4

    return score_count, scores


# Save high scores
def save_scores():
    
    global guesses
    
    #fetch scores
    score_count, scores = fetch_scores()
    #Increase the number of scores to be stored by one
    score_count +=1
    
    #Prompt user to input their name
    print("Congratulation, your guess is correct: "+str(actual_value)+"\n")
    user_name = input("Enter your name using 3 Letters:\n")
    #While loop to check whether the user has entered 3 letters
    i = 0
    while i != 1:
          if len(user_name) != 3:
             #Prompt user to enter their name again and remind them to only use 3 letters.   
             user_name = input("Error! Enter your name using 3 Letters:\n")
          else:
             #Increase the number of guesses by one.
             guesses+=1
             #Append the newly entered user name and score to scores.
             scores.append([user_name,guesses])
             #Sort the scores from lowest to highest.
             scores.sort(key=lambda x: x[1])
             #Write the new total number of scores to the EEPROM
             eeprom.write_byte(0, score_count)
             #Register to start writing scores from
             score_reg = 7
             #For loop on how to write to the EEPROM
             for i in range(0, score_count):
                 a = scores[i]
                 b = a[0]
                 c = 0
                 #For loop to write the names and scores to their corresponding registers.
                 for j in range((i+1)*4,(i+1)*4+3):
                     eeprom.write_byte(j, ord(b[c]))
                     c+=1
                     eeprom.write_byte(score_reg,a[1])
                     score_reg += 4
             #Reset the value guessed by the user
             guess_value = 0
             #Stop the buzzer and accuracy LED   
             Buzzer_pwm.stop()
             LED_red.stop()
             #Turn off binary LEDs
             GPIO.output(LED_value[0], GPIO.LOW)
             GPIO.output(LED_value[1], GPIO.LOW)
             GPIO.output(LED_value[2], GPIO.LOW)
             #Cleanup the GPIO, setup it up again and take the user back to the main menu.
             GPIO.cleanup()
             setup()
             menu()
    
    pass


# Generate guess number
def generate_number():
    return random.randint(0, pow(2, 3)-1)

# Increase button pressed
def btn_increase_pressed(channel):

# You can choose to have a global variable to store the user's current guess,
    global guess_value
    #Check if the guessed value is less than 8, then increase the guessed value by one.
    if guess_value<8:
       guess_value = guess_value+1
    #If the guessed value is greater than 8 then turn all the LEDs off
    else:
       guess_value = 0
       GPIO.output(LED_value[0], GPIO.LOW)
       GPIO.output(LED_value[1], GPIO.LOW)
       GPIO.output(LED_value[2], GPIO.LOW)

    # Increase the value shown on the LEDs by checking the guessed value and changing them accordingly
    if guess_value == 1:
       GPIO.output(LED_value[0], GPIO.LOW)
       GPIO.output(LED_value[1], GPIO.LOW)
       GPIO.output(LED_value[2], GPIO.HIGH)
    elif guess_value == 2:
       GPIO.output(LED_value[0], GPIO.LOW)
       GPIO.output(LED_value[1], GPIO.HIGH)
       GPIO.output(LED_value[2], GPIO.LOW)
    elif guess_value == 3:
       GPIO.output(LED_value[0], GPIO.LOW)
       GPIO.output(LED_value[1], GPIO.HIGH)
       GPIO.output(LED_value[2], GPIO.HIGH)
    elif guess_value == 4:
       GPIO.output(LED_value[0], GPIO.HIGH)
       GPIO.output(LED_value[1], GPIO.LOW)
       GPIO.output(LED_value[2], GPIO.LOW)
    elif guess_value == 5:
       GPIO.output(LED_value[0], GPIO.HIGH)
       GPIO.output(LED_value[1], GPIO.LOW)
       GPIO.output(LED_value[2], GPIO.HIGH)
    elif guess_value == 6:
       GPIO.output(LED_value[0], GPIO.HIGH)
       GPIO.output(LED_value[1], GPIO.HIGH)
       GPIO.output(LED_value[2], GPIO.LOW)
    elif guess_value == 7:
       GPIO.output(LED_value[0], GPIO.HIGH)
       GPIO.output(LED_value[1], GPIO.HIGH)
       GPIO.output(LED_value[2], GPIO.HIGH)
    
    pass


# Guess button
def btn_guess_pressed(channel):
    
    global guesses
    guesses = 0
    global guess_value
    global actual_value
    #Creating starting time when button is pressed.
    start_time = time.time()
    #Making sure the button isn't pressed.
    while GPIO.input(btn_submit) == 0:
          pass 
    #Calculate how long the button was pressed for.
    pressedTime = time.time()-start_time
    #If button was held down long enough then turn off buzzer and LED and 
    #cleanup the GPIO, setup it up again and take the user back to the main menu.
    if pressedTime > 0.5 :
       Buzzer_pwm.stop()
       LED_red.stop
       GPIO.cleanup()
       setup()
       menu()
    
    else:
       #If the user guessed correctly 
       if guess_value == actual_value:
          #Reset the guessed value back to zero  
          guess_value = 0
          #Increase the total guesses by 1  
          guesses+=1
          Buzzer_pwm.stop()
          LED_red.stop()
          #Go and save the score  
          save_scores()
            
       #If the uesr guessed wrong, then increase their guesses by one 
       #and indicate their accuracy with the buzzer and LED
       else:
          guesses+=1
          accuracy_leds()
          trigger_buzzer()
    pass


# LED Brightness
def accuracy_leds():
    # Set the brightness of the LED based on how close the guess is to the answer
    brightness = 0
    if guess_value>actual_value:
    # - If they guessed 7, the brightness would be at ((8-7)/(8-6)*100 = 50%
       brightness =(((8-guess_value)/(8-actual_value))*100)
       LED_red.start(brightness)
    elif guess_value<actual_value:
     # - For example if the answer is 6 and a user guesses 4, the brightness should be at 4/6*100 = 66%
       brightness=((guess_value/actual_value)*100)
       LED_red.start(brightness)
    # - The % brightness should be directly proportional to the % "closeness"
    elif guess_value == actual_value:
       LED_red.start(100)
    else:
       LED_red.start(brightness)
    pass

# Sound Buzzer
def trigger_buzzer():
    # The buzzer operates differently from the LED
    # While we want the brightness of the LED to change(duty cycle), we want the frequency of the buzzer to change
    # The buzzer duty cycle should be left at 50%
  
    # If the user is off by an absolute value of 3, the buzzer should sound once every second
    if abs(guess_value-actual_value) == 3:
       Buzzer_pwm.start(50)
       Buzzer_pwm.ChangeFrequency(1)
    # If the user is off by an absolute value of 2, the buzzer should sound twice every second
    elif abs(guess_value-actual_value) == 2:
       Buzzer_pwm.start(50)
       Buzzer_pwm.ChangeFrequency(2)
    # If the user is off by an absolute value of 1, the buzzer should sound 4 times a second
    elif abs(guess_value-actual_value) == 1:
       Buzzer_pwm.start(50)
       Buzzer_pwm.ChangeFrequency(4)
    else:
       pass


if __name__ == "__main__":
   #eeprom.populate_mock_scores()
    try:
        # Call setup function
        setup()
        # eeprom.clear(16)
        welcome()
        while True:
            menu()
            pass
    except Exception as e:
        print(e)
    finally:
        GPIO.cleanup()
