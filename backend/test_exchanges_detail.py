from tickflow import TickFlow

tf = TickFlow(api_key='tk_4d7e268030a5449abbcc59b28f6e76b8')
exchanges = tf.exchanges.list()

print(f'数量：{len(exchanges)}')
print(f'类型：{type(exchanges[0])}')
print(f'属性：{dir(exchanges[0])}')

if hasattr(exchanges[0], '__dict__'):
    print(f'值：{vars(exchanges[0])}')
else:
    print(f'值：{exchanges[0]}')
