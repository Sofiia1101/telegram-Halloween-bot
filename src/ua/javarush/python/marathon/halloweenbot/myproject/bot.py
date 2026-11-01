import os
from dotenv import load_dotenv
from telegram import Update
from telegram.error import BadRequest
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    CommandHandler,
    CallbackContext,
)
from ai import *
from util import *

load_dotenv()


async def start(update: Update, context: CallbackContext):
    session.mode = "main"

    text = load_message(session.mode)

    await send_photo(update, context, session.mode)
    await send_text(update, context, text)

    user_id = update.message.from_user.id
    create_user_dir(user_id)

    show_main_menu(update, context, {
        "start": "👨‍💼 Main bot menu",
        "image": "⚰️ Create image",
        "edit": "🧙 Edit image",
        "merge": "🕷️ Merge images",
        "party": "🎃 Photo for Halloween party",
        "video": "🎬☠️ Scary Halloween video",
    })


async def create_command(update: Update, context: CallbackContext):
    session.mode = "create"
    text = load_message(session.mode)

    await send_photo(update, context, session.mode)
    await send_text_buttons(update, context, text, buttons={
        "create_anime": "👧 Аніме",
        "create_photo": "📷 Фото",
    }, checkbox_key=session.image_type)


async def create_button(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    query = update.callback_query.data
    session.image_type = query

    session.mode = "create"

    text = load_message(session.mode)
    message = update.callback_query.message

    try:
        await edit_text_buttons(message, text, buttons={
            "create_anime": "👧 Аніме",
            "create_photo": "📷 Фото",
        }, checkbox_key=session.image_type)
    except BadRequest:
        pass


async def create_message(update: Update, context: CallbackContext):
    text = update.message.text
    user_id = update.message.from_user.id
    photo_path = f"resources/users/{user_id}/photo.jpg"

    prompt = load_prompt(session.image_type)
    ai_create_image(prompt=prompt + text, output_path=photo_path)
    await send_photo(update, context, photo_path)

async def edit_command(update: Update, context):
    session.mode = "edit"
    text = load_message(session.mode)

    await send_photo(update, context, session.mode)
    await send_text(update, context, text)

async def edit_message(update: Update, context):
    text = update.message.text
    user_id = update.message.from_user.id
    photo_path = f"resources/users/{user_id}/photo.jpg"

    if not os.path.exists(photo_path):
        await send_text(update, context, text="Спочатку завантажте або створіть зображення")
        return

    prompt = load_prompt(session.mode)

    ai_edit_image(input_image_path=photo_path, prompt=prompt + text, output_path=photo_path)
    await send_photo(update, context, photo_path)

async def save_photo(update: Update, context):
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)

    user_id = update.message.from_user.id
    photo_path = f"resources/users/{user_id}/photo.jpg"
    await file.download_to_drive(photo_path)

    await send_text(update, context, text="Фото підготовлене до роботи")

async def merge_command(update: Update, context):
    session.mode = "merge"
    session.image_list.clear()

    text = load_message(session.mode)

    await send_photo(update, context, session.mode)
    await send_text_buttons(update, context, text,{
        "merge_join": "Просто об'єднати зображення",
        "merge_first": "Додати всіх на перше зображення",
        "merge_last": "Додати всіх на останнє зображення",
    })

async def merge_add_photo(update, context):
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)

    image_count = len(session.image_list)+1
    user_id = update.message.from_user.id
    photo_path = f"resources/users/{user_id}/photo{image_count}.jpg"

    await file.download_to_drive(photo_path)
    session.image_list.append(photo_path)
    await send_text(update, context, text=f"{image_count} фото підготовлено до роботи")


async def merge_button(update: Update, context):
    await update.callback_query.answer()
    query = update.callback_query.data

    user_id = update.callback_query.from_user.id
    result_path = f"resources/users/{user_id}/result.jpg"

    if len(session.image_list) < 2:
        await send_text(update, context, text="Спочатку завантажте ваше фото")
        return

    prompt = load_prompt(query)
    ai_merge_image(input_image_path_list=session.image_list, prompt=prompt, output_path=result_path)

    await send_photo(update, context, result_path)

async def party_command(update: Update, context):
    session.mode = "party"
    text = load_message(session.mode)

    await send_photo(update, context, session.mode)
    await send_text_buttons(update, context, text, {
        "party_image1": "🌕 Місячне затемнення (перевертень) ",
        "party_image2": "🩸 Прокляте дзеркало (вампір) ",
        "party_image3": "🧙‍♀️ Відьмине коло (дим і руни) ",
        "party_image4": "🧟 Гниття часу (зомбі) ",
        "party_image5": "😈 Пентаграма призову (демон)",
    })

async def video_button(update: Update, context):
    await update.callback_query.answer()
    query = update.callback_query.data

    user_id = update.callback_query.from_user.id
    photo_path = f"resources/users/{user_id}/photo.jpg"
    video_path = f"resources/users/{user_id}/video.mp4"

    if not os.path.exists(photo_path):
        await send_text(update, context, text="Спочатку завантажте ваше фото")
        return

    prompt = load_prompt(query)
    await send_text(update, context, text="Генерація відео займе близько 20 секунд")

    ai_video_from_text_and_image(input_image_path=photo_path, prompt=prompt, out_path=video_path)
    await send_video(update, context, video_path)

async def party_button(update: Update, context):
    await update.callback_query.answer()
    query = update.callback_query.data

    user_id = update.callback_query.from_user.id
    photo_path = f"resources/users/{user_id}/photo.jpg"
    result_path = f"resources/users/{user_id}/result.jpg"

    if not os.path.exists(photo_path):
        await send_text(update, context, text="Спочатку завантажте ваше фото")
        return


    prompt = load_prompt(query)
    ai_edit_image(input_image_path=photo_path, prompt=prompt, output_path=result_path)
    await send_photo(update, context, result_path)

async def video_command(update: Update, context):
    session.mode = "video"
    text = load_message(session.mode)

    await send_photo(update, context, session.mode)
    await send_text_buttons(update, context, text, {
        "video1": "🐺 Місячне затемнення (перевертень) ",
        "video2": "🦇 Прокляте дзеркало (вампір) ",
        "video3": "🔮 Відьмине коло (дим і руни) ",
        "video4": "🧟 Гниття часу (зомбі) ",
        "video5": "👹 Призов демона (демон)",
    })

async def on_message(update: Update, context: CallbackContext):
    if session.mode == "create":
        await create_message(update, context)
    elif session.mode == "edit":
        await edit_message(update, context)
    else:
        await send_text(update, context, text="Hi")
        await send_text(update, context, text="You texted: " + update.message.text)


async def on_photo(update, context):
        if session.mode == "merge":
            await merge_add_photo(update, context)
        else:
            await save_photo(update, context)


app = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()

session.mode = None
session.image_type = "create_anime"
session.image_list = []

app.add_error_handler(error_handler)


app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("image", create_command))
app.add_handler(CommandHandler("edit", edit_command))
app.add_handler(CommandHandler("merge", merge_command))
app.add_handler(CommandHandler("party", party_command))
app.add_handler(CommandHandler("video", video_command))
app.add_handler(CallbackQueryHandler(create_button, pattern="^create_.*"))
app.add_handler(CallbackQueryHandler(merge_button, pattern="^merge_.*"))
app.add_handler(CallbackQueryHandler(party_button, pattern="^party.*"))
app.add_handler(CallbackQueryHandler(video_button, pattern="^video.*"))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
app.add_handler(MessageHandler(filters.PHOTO & ~filters.COMMAND, on_photo))

app.run_polling()