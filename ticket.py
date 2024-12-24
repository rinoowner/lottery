import telebot
from telebot import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telebot.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext
import random

# Fixed Owner and Admin User IDs
OWNER_ID = 1351184742  # Replace with your Telegram User ID
ADMIN_ID = 6037699129  # Replace with your Admin's Telegram User ID

# Define a dictionary to store user tickets
user_tickets = {}

# Define a list to store approved user IDs
approved_users = []

# Track the number of tickets sold
tickets_sold = 0
max_tickets = 10

# QR code link for payment
QR_CODE_LINK = "https://drive.google.com/uc?export=view&id=1L1iBz3ZPvaVC0s3CS8HGr_TIKrfzu3DU"

# Define the bot's start command handler
async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    welcome_message = (
        f"\U0001F389 Hello {user.first_name}! \U0001F389\n\n"
        "Welcome to the Lottery Bot! \U0001F4B0\n\n"
        "Here's how it works:\n"
        "\u2022 Buy a lottery ticket for just ₹10. \U0001F4B8\n"
        "\u2022 Stand a chance to win ₹50! \U0001F911\n\n"
        "How to participate:\n"
        "1️⃣ Click the button below to get the QR code for payment.\n"
        "2️⃣ After making the payment, send the payment screenshot to @ticket_adminbot\n"
        "3️⃣ Your ticket will be approved within 1 hour.\n\n"
        "\U0001F3C6 Good luck and happy playing! \U0001F3C6"
    )

    keyboard = [
        [InlineKeyboardButton("\U0001F4B3 Buy Ticket", callback_data="buy_ticket")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

# Callback handler for "Buy Ticket" button
async def handle_buy_ticket(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    await query.message.reply_photo(
        photo=QR_CODE_LINK,
        caption=(
            "\U0001F4B3 Please scan the QR code above to pay ₹10 and participate in the lottery.\n\n"
            "After payment, send the screenshot to @ticket_adminbot for ticket approval."
        ),
    )

# Define the approve ticket command for admins and owner
async def approve_ticket(update: Update, context: CallbackContext):
    global tickets_sold
    user_id = update.effective_user.id

    # Check if the user is owner or admin
    if user_id != OWNER_ID and user_id != ADMIN_ID:
        await update.message.reply_text("❌ You don't have permission to approve tickets.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Usage: /approve <user_id>")
        return

    approve_user_id = context.args[0]

    try:
        if approve_user_id not in user_tickets:
            # Generate a ticket for the user
            ticket_number = f"TICKET-{approve_user_id}-{len(user_tickets) + 1}"
            user_tickets[approve_user_id] = ticket_number
            approved_users.append(approve_user_id)

            # Increment ticket count
            tickets_sold += 1

            await context.bot.send_message(
                chat_id=approve_user_id,
                text=(
                    f"\U0001F389 Congratulations! \U0001F389\n"
                    f"Your ticket has been approved. \U0001F3C6\n"
                    f"Here is your ticket number: {ticket_number}\n\n"
                    "Best of luck for the draw! \U0001F3C6"
                ),
            )
            await update.message.reply_text(
                f"User {approve_user_id} has been successfully approved with ticket {ticket_number}."
            )

            # Check if we have 10 approved tickets
            if tickets_sold >= max_tickets:
                await conduct_draw(context)
        else:
            await update.message.reply_text("User is already approved.")

    except Exception as e:
        await update.message.reply_text(f"Failed to approve user {approve_user_id}: {e}")

# Define the function to conduct the draw
async def conduct_draw(context: CallbackContext):
    global tickets_sold
    PRIZE_AMOUNT = "₹50"
    winner_id = random.choice(approved_users)
    winner_name = (await context.bot.get_chat(winner_id)).first_name
    winner_ticket = user_tickets[winner_id]

    # Announce the winner
    for user_id in user_tickets:
        name = (await context.bot.get_chat(user_id)).first_name
        if user_id == winner_id:
            await context.bot.send_message(
                chat_id=user_id,
                text=(
                     f"\U0001F3C6 The draw is complete! \U0001F3C6\n\n"
                    f"\U0001F389 Congratulations to {winner_name} \U0001F389\n"
                    f"Ticket Number: {winner_ticket}\n\n"
                    f"They have won the grand prize of {PRIZE_AMOUNT}! \U0001F911\n\n"
                    "Thank you for participating. Stay tuned for the next round!"
                ),
            )
        else:
            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    "\U000026A0 Unfortunately, you didn't win this round.\n"
                    "But don't worry, you can buy another ticket for the next round! \U0001F4B8"
                ),
            )

    # Reset everything after the draw
    reset_after_draw()

# Function to reset after the draw
def reset_after_draw():
    global approved_users, user_tickets, tickets_sold
    approved_users.clear()
    user_tickets.clear()
    tickets_sold = 0  # Reset ticket count

# Define the view ticket command for users
async def view_ticket(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)

    if user_id in user_tickets:
        await update.message.reply_text(
            f"\U0001F4B0 Your Ticket:\n\nTicket Number: {user_tickets[user_id]}\n\nBest of luck! \U0001F3C6"
        )
    else:
        await update.message.reply_text(
            "\U000026A0 You do not have an approved ticket yet. Please buy a ticket from the @ticket_adminbot"
        )

# Add this function to track and display the total tickets sold:
async def view_tickets_sold(update: Update, context: CallbackContext):
    await update.message.reply_text(f"Total tickets sold: {tickets_sold} / {max_tickets}")

# Define a broadcast message command for the owner
async def broadcast(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    # Check if the user is the owner
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ Only the owner can use this command.")
        return

    message = " ".join(context.args)
    if not message:
        await update.message.reply_text("Usage: /broadcast <message>")
        return

    for user_id in user_tickets.keys():
        await context.bot.send_message(chat_id=user_id, text=message)

    await update.message.reply_text("✅ Broadcast message sent successfully.")

# Set up the bot
def main():
    # Replace 'YOUR_TOKEN' with your bot's token
    application = Application.builder().token("7125867291:AAH0E-hN5tAwGgVPpGqhfpxg3mYBGT41dDY").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_buy_ticket, pattern="^buy_ticket$"))
    application.add_handler(CommandHandler("approve", approve_ticket))
    application.add_handler(CommandHandler("viewticket", view_ticket))
    application.add_handler(CommandHandler("viewticketsold", view_tickets_sold))
    application.add_handler(CommandHandler("broadcast", broadcast))

    application.run_polling()

if __name__ == "__main__":
    main()
