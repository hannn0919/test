from flask import redirect, render_template, url_for, flash, request, abort
from flask.views import MethodView
from flask_login import login_user, current_user, logout_user
from flask_wtf import FlaskForm

from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import InputRequired, Length, ValidationError

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage, ButtonsTemplate, CarouselColumn, CarouselTemplate, URITemplateAction

from app.models.keyword import Keyword
from app.models.product import Product
from app import app

import os, datetime

class SearchView(MethodView):
    def get(self):
        if request.args.get('way') == "bidding":
            products = Product.objects(name__icontains=request.args.get('keyword'), bid__due_time__gt=datetime.datetime.utcnow()+datetime.timedelta(hours=8), status=0, bidding=True)
            way = "bidding"
        elif request.args.get('way') == "normal":
            products = Product.objects(name__icontains=request.args.get('keyword'), status=0, bidding=False)
            way = "normal"
        else:
            abort(404)

        if request.args.get('keyword') not in ["", None]:
            keyword = Keyword.objects(keyword=request.args.get('keyword')).first()
            if keyword == None:
                keyword = Keyword(keyword=request.args.get('keyword'))
            keyword.count += 1
            keyword.save()

        return render_template('search.html', products=products, way=way, now=datetime.datetime.utcnow()+datetime.timedelta(hours=8))

line_bot_api = LineBotApi(app.config['LINE_CHATBOT_ACCESS_TOKEN'])
handler = WebhookHandler(app.config['LINE_CHATBOT_SECRET'])

class LineChatbotSearch(MethodView):
    def post(self):

        # get X-Line-Signature header value
        signature = request.headers['X-Line-Signature']

        # get request body as text
        body = request.get_data(as_text=True)
        app.logger.info("Request body: " + body)
        # handle webhook body
        try:
            handler.handle(body, signature)
        except InvalidSignatureError:
            print("Invalid signature. Please check your channel access token/channel secret.")
            abort(400)

        return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.message.text == None:
        products = Product.objects(status=0)
    else:
        products = Product.objects(name__icontains=event.message.text, status=0)

    carouselColumns = [];

    count = 0
    for product in products:
        # imagePath ='./app/static/image/' + str(product.id) + '/' + product.image
        # if os.path.isfile(imagePath):
        #   image = imagePath
        # else:
        #   image = "https://miro.medium.com/max/2834/0*f81bU2qWpP51WWWC.jpg"
        filePath = 'image/' + str(product.id) + '/' + product.image        
        if(product.bidding):
            price = "Last Bid: NT$" + str(product.bid.now_price)
        else:
            price = "NT$" + str(product.price)
        carouselColumns.append(
            CarouselColumn(
                thumbnail_image_url=request.host_url[:-1] + url_for('static', filename=filePath),
                title=product.name,
                text=price,
                actions=[
                    URITemplateAction(
                        label='Take a look!',
                        uri=request.host_url[:-1] + url_for('show_normal', product_id=product.id)
                    )
                ]               
            ))
        count += 1
        if count > 5:
            break

    if carouselColumns:
        message = TemplateSendMessage(
            alt_text="請到 "+ request.url_root[:-1] + url_for('search', keyword=event.message.text) + " 或",
            template=CarouselTemplate(columns=carouselColumns)
        )
    else:       
        message = TextSendMessage(text="找不到相關商品")
    line_bot_api.reply_message(event.reply_token, message)

# @LineChatbotSearch.handler.add(MessageEvent, message=TextMessage)
# def handle_message(event):
#     line_bot_api.reply_message(
#         event.reply_token,
#         TextSendMessage(text=event.message.text))