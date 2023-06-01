from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO, join_room, emit, leave_room

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///identifier.sqlite'  # 数据库地址
db = SQLAlchemy(app)
migrate = Migrate(app, db)

socketio = SocketIO(app)


# 定义消息模型
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(255))
    name = db.Column(db.String(50))
    room = db.Column(db.String(50))  # 添加房间字段


@app.route('/')
def index():
    messages = Message.query.all()
    return render_template('index.html', message=messages)


@socketio.on('join')
def handle_join(data):
    room = data['room']
    join_room(room)
    emit('message', {'text': f'User joined room: {room}'}, room=room)


@socketio.on('leave')
def handle_leave(data):
    room = data['room']
    leave_room(room)
    emit('message', {'text': f'User left room: {room}'}, room=room)


@socketio.on('message')
def handle_message(data):
    room = data['room']
    text = data['text']
    name = data['name']
    message = Message(text=text, name=name, room=room)  # 创建消息对象并指定房间
    db.session.add(message)  # 将消息对象添加到会话中
    db.session.commit()  # 提交会话，将消息保存到数据库
    emit('message', {'text': text, 'name': name}, room=room)


@app.route('/messages', methods=['GET'])
def get_messages():
    username = request.args.get('username')  # 获取请求参数中的username
    if username:
        messages = Message.query.filter_by(name=username).all()  # 根据username过滤消息
    else:
        messages = Message.query.all()  # 获取所有消息
    return {'messages': [{'text': message.text, 'name': message.name, 'room': message.room} for message in messages]}


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        socketio.run(app.run(host='0.0.0.0', port=2333))
