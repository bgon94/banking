from datetime import datetime
from tracemalloc import start
from venv import create
import mysql.connector
from mysql.connector import Error
import config
import re
import random
import time

mydb = mysql.connector.connect(
    host=config.HOST,
    user=config.USER,
    passwd=config.PASS,
    database=config.DB
)

mycursor = mydb.cursor()


def get_date():
    now = datetime.now()
    formatted_date = now.strftime('%Y-%m-%d')
    return formatted_date


def create_user():
    while (True):
        username = input("Please enter a username: ")
        while True:
            password = input("Please enter a password: ")
            if len(password) < 8:
                print("Make sure your password is at lest 8 letters")
            elif re.search('[0-9]', password) is None:
                print("Make sure your password has a number in it")
            elif re.search('[A-Z]', password) is None:
                print("Make sure your password has a capital letter in it")
            elif re.search('[!@#$%^&*]', password) is None:
                print("Make sure your password has a special character: !@#$%^&* ")
            else:
                break
        starting_balance = input("Please enter your starting balance: ")
        account_num = random.randint(100001, 199999)
        sql = "INSERT INTO users (account_number, username,password,balance) VALUES (%s,%s,%s,%s)"
        val = (account_num, username, password, starting_balance)
        try:
            mycursor.execute(sql, val)
            mycursor.fetchone()
            mydb.commit()
            print("User account submitted successfully.")
            print(f"Username: {username}")
            print(f"Account number: {account_num}")
            print(f"Starting balance: {starting_balance}")
            return
        except Exception as e:
            err_code = e.args[0]
            if err_code == 1062:
                print("Username already exists.  Please use a different one.")


def delete_all_users():
    sql = "DELETE FROM users"
    mycursor.execute(sql)
    mydb.commit()


def login_page():
    print("=== Welcome to Money Tree ===")
    print("1.    Login")
    print("2.    Register")
    print("3.    Delete all users")
    print("4.    Quit")


def account_page():
    print("=== Money Tree ===")
    print("1.    Check Balance")
    print("2.    Deposit")
    print("3.    Withdraw")
    print("4.    Send Money")
    print("5.    Logout")


def login():
    print("=== Login ===")
    username = input("Enter your username: ")
    password = input("Please enter your password: ")
    mycursor.execute(
        "SELECT * FROM users WHERE username = %s AND password = %s", (username, password,))
    account = mycursor.fetchone()
    if account:
        print(f"Login Successful.  Welcome {username}")
        return True, account
    else:
        print("Incorrect username or password")
        return False, ""


def check_balance(login_row):
    account_num = login_row[0]
    username = login_row[1]
    mycursor.execute(
        "SELECT balance,account_number FROM users WHERE username = %s", (username,))
    pulled_balance = mycursor.fetchone()
    print(f"Account number: {pulled_balance[1]}")
    print(f"Your current balance is {pulled_balance[0]}")


def deposit(login_row):
    current_date = get_date()
    username = login_row[1]
    mycursor.execute(
        "SELECT balance FROM users WHERE username = %s", (username,))
    pulled_balance = mycursor.fetchone()
    pulled_balance = pulled_balance[0]
    while (True):
        deposit_amount = input("Enter amount to deposit: ")
        if deposit_amount.isdigit():
            deposit_amount = float(deposit_amount)
            break
        else:
            print("Please only use numbers")

    new_balance = deposit_amount + pulled_balance
    mycursor.execute(
        "UPDATE users SET balance = %s WHERE username = %s", (new_balance, username,))
    mycursor.execute(
        "INSERT INTO transactions (date,sender_username,transaction_type,amount) VALUES (%s,%s,'Deposit',%s)", (current_date, username,deposit_amount,))
    mydb.commit()
    print(f"{deposit_amount } has been successfully deposited")


def withdraw(login_row):
    current_date = get_date()
    username = login_row[1]
    mycursor.execute(
        "SELECT balance FROM users WHERE username = %s", (username,))
    pulled_balance = mycursor.fetchone()
    pulled_balance = pulled_balance[0]

    while (True):
        withdraw_amount = input("Enter amount to withdraw: ")
        if withdraw_amount.isdigit():
            withdraw_amount = float(withdraw_amount)
            if withdraw_amount > pulled_balance:
                print("You do not have suffient funds for this withdraw")
            else:
                break
        else:
            print("Please only use numbers")

    new_balance = pulled_balance - withdraw_amount
    mycursor.execute(
        "UPDATE users SET balance = %s WHERE username = %s", (new_balance, username,))
    mycursor.execute(
        "INSERT INTO transactions (date,sender_username,transaction_type,amount) VALUES (%s,%s,'Withdraw',%s)", (current_date, username,withdraw_amount,))
    mydb.commit()
    print(f"{withdraw_amount } has been successfully withdrawn")


def send_money(login_row):
    current_date = get_date()
    username = login_row[1]
    mycursor.execute(
        "SELECT balance FROM users WHERE username = %s", (username,))
    pulled_balance = mycursor.fetchone()
    pulled_balance = pulled_balance[0]
    while (True):
        recipient_input = input("Enter recipients username: ")
        mycursor.execute(
            "SELECT balance,username FROM users WHERE username = %s", (recipient_input,))
        row = mycursor.fetchone()
        if row == None:
            print("Recipient does not exist")
            continue
        db_recipient_username = row[1]
        db_recipient_balance = row[0]

        if recipient_input == db_recipient_username:
            while (True):
                send_amount = input("Please enter amount to send: ")
                if not send_amount.isdigit():
                    print("Please only use numbers")
                    continue
                send_amount = float(send_amount)
                if send_amount > pulled_balance:
                    print("You do not have sufficient funds for this transaction")
                    continue
                user_confirmation = input(
                    f"You are about to send {send_amount} to {db_recipient_username}. Please type 'y' to confirm or 'n' to cancel: ")
                if user_confirmation == "y":
                    new_recipient_balance = db_recipient_balance + send_amount
                    pulled_balance = pulled_balance - send_amount
                    mycursor.execute("UPDATE users SET balance = %s WHERE username = %s",
                                     (new_recipient_balance, db_recipient_username,))

                    mycursor.execute(
                        "UPDATE users SET balance = %s WHERE username = %s", (pulled_balance, username,))
                    mycursor.execute(
                        "INSERT INTO transactions (date,sender_username,receiver_username,transaction_type,amount) VALUES (%s,%s,%s,'Transfer',%s)", (current_date, username, db_recipient_username,send_amount,))
                    mydb.commit()
                    print("Money successfully sent.")
                    return
                else:
                    print("Transaction cancelled")
                    return
        else:
            print("Recipient does not exist")


while (True):
    login_page()
    user_input = input(">> ")
    if user_input == "1":
        login_result = login()
        login_check = login_result[0]
        login_row = login_result[1]
        if login_check:
            while (True):
                account_page()
                account_user_input = input(">> ")
                if account_user_input == "1":
                    check_balance(login_row)
                if account_user_input == "2":
                    deposit(login_row)
                if account_user_input == "3":
                    withdraw(login_row)
                if account_user_input == "4":
                    send_money(login_row)
                if account_user_input == "5":
                    print("Log off successful")
                    break
    elif user_input == "2":
        create_user()
    elif user_input == "3":
        delete_all_users()
    elif user_input == "4":
        exit()
