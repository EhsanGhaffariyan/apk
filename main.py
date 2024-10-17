from flet import *
import asyncio
import threading
import websockets
import json
import sqlite3

def main(page: Page):
    # page.adaptive = True
    page.title = "GoldenTrendFX.com - Position Calculator"
    page.theme_mode = ThemeMode.LIGHT
    page.scroll = ScrollMode.AUTO
    loop = asyncio.new_event_loop()
    def start_loop():
        asyncio.set_event_loop(loop)
        loop.run_forever()
    threading.Thread(target=start_loop, daemon=True).start()

    server_address = ''
    server_port = ''

    def init_database():
        conn = sqlite3.connect('config.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS server_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                address TEXT NOT NULL,
                port TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    def get_server_config():
        conn = sqlite3.connect('config.db')
        cursor = conn.cursor()
        cursor.execute('SELECT address, port FROM server_config ORDER BY id DESC LIMIT 1')
        result = cursor.fetchone()
        conn.close()
        return result

    def save_server_config(address, port):
        conn = sqlite3.connect('config.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO server_config (address, port) VALUES (?, ?)', (address, port))
        conn.commit()
        conn.close()

    def show_server_config_dialog():
        address_field = TextField(label='Server Address', value='ws://localhost', expand=1)
        port_field = TextField(label='Port', value='8080', expand=1)

        def on_submit(e):
            nonlocal server_address, server_port
            server_address = address_field.value.strip()
            server_port = port_field.value.strip()
            if server_address and server_port:
                save_server_config(server_address, server_port)
                dlg.open = False
                page.update()
                initialize_app()
            else:
                page.snack_bar = SnackBar(Text('Please enter both server address and port.'), open=True)
                page.snack_bar.open = True
                page.update()

        dlg = AlertDialog(
            title=Text("Server Configuration"),
            content=Column([address_field, port_field]),
            actions=[
                TextButton("Submit", on_click=on_submit)
            ],
            modal=True
        )
        dialog = dlg
        dlg.open = True
        page.update()

    def initialize_app():
        nonlocal server_address, server_port

        if not server_address or not server_port:
            show_server_config_dialog()
            return


        balance_info = TextField(
            height=50,
            read_only=True,
            content_padding=10,
            suffix_text="$",
            label="Balance",
            value="0.0",
            expand=1
        )
        equity_info = TextField(
            height=50,
            read_only=True,
            content_padding=10,
            suffix_text="$",
            label="Equity",
            value="0.0",
            expand=1
        )
        margin_free_info = TextField(
            height=50,
            read_only=True,
            content_padding=10,
            suffix_text="$",
            label="Free Margin",
            value="0.0",
            expand=1
        )
        margin_level_info = TextField(
            height=50,
            read_only=True,
            content_padding=10,
            suffix_text="%",
            label="Margin Level",
            value="0.0",
            expand=1
        )

        summary_row = Row([
            balance_info,
            equity_info,
            margin_free_info,
            margin_level_info
        ])

        symbol_search = TextField(label='Search Symbol', expand=1)
        symbol_name = Dropdown(label='Symbol', options=[], expand=1)
        spread_text = Text('Spread: -')

        risk_slider = Slider(min=0.01, max=5.0, value=1.0, expand=1)
        risk_text = Text(f"Risk: {risk_slider.value:.2f}% (0.00$)")

        order_action = Dropdown(
            label='Action Type',
            options=[
                dropdown.Option('Market Order'),
                dropdown.Option('Pending Order')
            ],
            value='Market Order',
            expand=1
        )
        entry_input = TextField(label='Entry Price', disabled=True, expand=1)

        stop_type = RadioGroup(content=Row([
            Radio(value='point', label='Point'),
            Radio(value='price', label='Price')
        ]), value='point')
        stop_loss_input = TextField(label='Stop Loss', expand=1)
        profit_dropdown = Dropdown(
            label='Profit Ratio',
            options=[
                dropdown.Option('1:1'),
                dropdown.Option('1:2'),
                dropdown.Option('1:3'),
                dropdown.Option('1:4'),
                dropdown.Option('1:5')
            ],
            value='1:2',
            expand=1
        )
        open_order_switch = Switch(label='Open Order', value=False)
        fill_policy = RadioGroup(content=Row([
            Radio(value='Immediate or Cancel', label='Immediate or Cancel'),
            Radio(value='Fill or Kill', label='Fill or Kill')
        ]), value='Immediate or Cancel', visible=False)

        buy_button = ElevatedButton('BUY', bgcolor='blue', color='white', on_click=lambda e: calculate_position_handler('BUY'), expand=1)
        sell_button = ElevatedButton('SELL', bgcolor='red', color='white', on_click=lambda e: calculate_position_handler('SELL'), expand=1)

        initial_risk_input = TextField(
            label="Initial Risk",
            height=50,
            content_padding=10,
            suffix_text="$",
            value="5",
            expand=1,
        )
        max_risk_input = TextField(
            label="Max Risk",
            value="20",
            height=50,
            content_padding=10,
            suffix_text="$",
            expand=1,
        )
        daily_target_input = TextField(
            label="Daily Profit Target",
            height=50,
            content_padding=10,
            suffix_text="$",
            value="100",
            expand=1,
        )

        total_today_profit = TextField(
            label="Today Net Profit",
            height=50,
            content_padding=10,
            suffix_text="$",
            expand=1,
            read_only= True
        )

        result_text = Text("")

        trades_list_view = ListView(
            expand=1,
            spacing=10,
            padding=10,
            auto_scroll=True
        )

        current_symbol = None
        async def send_request(action, params=None):
            uri = f'{server_address}:{server_port}'
            try:
                async with websockets.connect(uri) as websocket:
                    request = {'action': action, 'params': params}
                    await websocket.send(json.dumps(request))
                    response = await websocket.recv()
                    return json.loads(response)
            except Exception as e:
                return {'status': 'error', 'message': str(e)}

        async def search_symbol_async(e):
            search_text = symbol_search.value.lower()
            response = await send_request('get_symbols')
            if response['status'] == 'success':
                symbols = response['result']
                filtered_symbols = [symbol for symbol in symbols if search_text in symbol.lower()]
                symbol_name.options = [dropdown.Option(symbol) for symbol in filtered_symbols]
                page.update()
            else:
                await show_alert(f"Error: {response['message']}")

        def search_symbol(e):
            asyncio.run_coroutine_threadsafe(search_symbol_async(e), loop)

        async def update_price_and_symbol():
            nonlocal current_symbol
            symbol = symbol_name.value
            if symbol:
                current_symbol = symbol
                response = await send_request('get_symbol_info', {'symbol_name': symbol})
                if response['status'] == 'success':
                    symbol_info = response['result']
                    spread = symbol_info.get('spread', '-')
                    spread_text.value = f"Spread: {spread}"
                    page.update()
                else:
                    await show_alert(f"Error: {response['message']}")
                await update_live_prices_once()
            else:
                current_symbol = None

        async def update_live_prices_once():
            symbol = current_symbol
            if symbol:
                response = await send_request('get_live_prices', {'symbol_name': symbol})
                if response['status'] == 'success':
                    prices = response['result']
                    ask_price = prices.get('ask', '-')
                    bid_price = prices.get('bid', '-')
                    spread = prices.get('spread', '-')
                    buy_button.text = f"BUY {ask_price}"
                    sell_button.text = f"SELL {bid_price}"
                    spread_text.value = f"Spread: {spread}"
                    page.update()
                else:
                    await show_alert(f"Error: {response['message']}")

        def symbol_changed(e):
            asyncio.run_coroutine_threadsafe(update_price_and_symbol(), loop)

        def toggle_entry_input(e):
            entry_input.disabled = (order_action.value == 'Market Order')
            if entry_input.disabled:
                entry_input.value = ''
            page.update()

        def toggle_fill_policy(e):
            fill_policy.visible = open_order_switch.value
            page.update()

        async def calculate_position_async(position_type):
            if order_action.value == 'Market Order':
                entry_value = ''
            else:
                entry_value = entry_input.value

            balance = float(balance_info.value)
            risk_percent = risk_slider.value
            risk_amount = (risk_percent / 100) * balance

            params = {
                'balance': balance,
                'symbol_name': symbol_name.value,
                'risk_position': risk_amount,
                'stop_type': stop_type.value,
                'stop_value': stop_loss_input.value,
                'profit_value': profit_dropdown.value.split(':')[1],
                'open_order_param': open_order_switch.value,
                'position_action': position_type,
                'entry_value': entry_value,
                'fill_policy_value': fill_policy.value,
                'order_action': order_action.value
            }

            response = await send_request('calculate_position', params)
            if response['status'] == 'success':
                result = response['result']
                if 'error' in result:
                    await show_alert(result['error'])
                else:
                    await show_result(result)
                    await update_risk()
            else:
                await show_alert(f"Error: {response['message']}")

        def calculate_position_handler(position_type):
            asyncio.run_coroutine_threadsafe(calculate_position_async(position_type), loop)

        async def show_alert(message):
            dlg = AlertDialog(title=Text("Error"), content=Text(message, selectable=True))
            dialog = dlg
            dlg.open = True
            page.update()
            await dlg.wait_closed()

        async def show_result(result):
            content = '\n'.join([f"{key}: {value}" for key, value in result.items()])
            dlg = AlertDialog(title=Text("Calculation Result"), content=Text(content))
            page.dialog = dlg
            dlg.open = True
            page.update()
            await dlg.wait_closed()

        async def update_live_prices():
            nonlocal current_symbol
            while True:
                symbol = current_symbol
                if symbol:
                    response = await send_request('get_live_prices', {'symbol_name': symbol})
                    if response['status'] == 'success':
                        prices = response['result']
                        ask_price = prices.get('ask', '-')
                        bid_price = prices.get('bid', '-')
                        spread = prices.get('spread', '-')
                        buy_button.text = f"BUY {ask_price}"
                        sell_button.text = f"SELL {bid_price}"
                        spread_text.value = f"Spread: {spread}"
                        page.update()
                    else:
                        await show_alert(f"Error: {response['message']}")
                await asyncio.sleep(0)

        async def update_account_info_async():
            while True:
                response = await send_request('get_account_info')
                if response['status'] == 'success':
                    account_info = response['result']
                    balance_info.value = str(account_info['balance'])
                    equity_info.value = str(account_info['equity'])
                    margin_free_info.value = str(account_info['free_margin'])
                    margin_level_info.value = str(account_info['margin_level'])
                    page.update()
                    await update_risk()
                else:
                    await show_alert(f"Error: {response['message']}")
                await asyncio.sleep(0)


        async def update_risk():
            initial_risk_per_trade = float(initial_risk_input.value)
            max_risk_per_trade = float(max_risk_input.value)
            balance = float(balance_info.value)

            params = {
                'initial_risk_per_trade': initial_risk_per_trade,
                'max_risk_per_trade': max_risk_per_trade
            }

            response = await send_request('calculate_next_risk', params)
            if response['status'] == 'success':
                result = response['result']
                if 'error' in result:
                    next_risk = initial_risk_per_trade
                else:
                    next_risk = result['next_risk']

                next_risk = min(next_risk, max_risk_per_trade)

                risk_percent = (next_risk / balance) * 100

                max_risk_percent = (max_risk_per_trade / balance) * 100
                risk_percent = min(risk_percent, max_risk_percent)

                risk_slider.max = max_risk_percent

                risk_slider.value = risk_percent

                risk_text.value = f"Risk: {risk_percent:.2f}% ({next_risk:.2f}$)"
                page.update()

                trades = result.get('trades', [])
                trades_list_view.controls.clear()

                total_net_profit = 0

                for trade in trades:
                    try:
                        net_profit = float(trade.get('net_profit', '0'))
                        profit_color = 'blue' if net_profit >= 0 else 'red'
                        trade_type_color = 'blue' if trade.get('trade_type', '').lower() == 'buy' else 'red'
                        total_net_profit += net_profit

                        def show_trade_dialog(e):
                            trade_dialog = AlertDialog(
                                title=Text(f"Trade Details - {trade.get('symbol', '')}"),
                                content=Column([
                                    Text(f"Symbol: {trade.get('symbol', '')}"),
                                    Text(f"Type: {trade.get('trade_type', '')}"),
                                    Text(f"Volume: {trade.get('volume', '')}"),
                                    Text(f"Entry Price: {trade.get('entry_price', '')}"),
                                    Text(f"Exit Price: {trade.get('exit_price', '')}"),
                                    Text(f"Profit: {trade.get('profit', '')}"),
                                    Text(f"Net Profit: {net_profit:.2f}", color=profit_color),
                                    Text(f"Commission: {trade.get('commission', '')}"),
                                    Text(f"Time: {trade.get('time', '')}"),
                                ]),
                                actions=[
                                    TextButton("Close", on_click=lambda e: close_trade_dialog(trade_dialog))
                                ],
                                modal=True,
                            )
                            page.dialog = trade_dialog
                            trade_dialog.open = True
                            page.update()

                        def close_trade_dialog(dialog):
                            dialog.open = False
                            page.update()

                        trade_tile = ListTile(
                            title=Row([
                                Text(f"{trade.get('symbol', '')}", weight="bold"),
                                Text(f" {trade.get('trade_type', '')}", color=trade_type_color, weight="bold"),
                                Text(f" {trade.get('volume', '')}", weight="bold"),
                            ]),

                            subtitle=Column([
                                Text(f"{trade.get('entry_price', '')} → {trade.get('exit_price', '')}", size=16),
                                Text(f"{trade.get('time', '')}", size=14),
                            ]),

                            trailing=Text(
                                f"{net_profit:.2f}",
                                color=profit_color,
                                weight="bold",
                                size=18
                            ),

                            on_click=show_trade_dialog
                        )

                        trades_list_view.controls.append(trade_tile)
                    except Exception as ex:
                        await show_alert(f"Error processing trade: {ex}")

                total_today_profit.value = total_net_profit

                page.update()


            else:
                await show_alert(f"Error: {response['message']}")

        def update_risk_slider():
            balance = float(balance_info.value)
            initial_risk_per_trade = float(initial_risk_input.value)
            max_risk_per_trade = float(max_risk_input.value)

            if balance > 0:
                initial_risk_percent = (initial_risk_per_trade / balance) * 100
                max_risk_percent = (max_risk_per_trade / balance) * 100
                risk_slider.max = max_risk_percent
                risk_slider.value = min(initial_risk_percent, max_risk_percent)
                update_risk_text(None)
                page.update()

        def update_risk_text(e):
            balance = float(balance_info.value)
            risk_percent = risk_slider.value

            risk_amount = (risk_percent / 100) * balance

            risk_text.value = f"Risk: {risk_percent:.2f}% ({risk_amount:.2f}$)"
            page.update()

        async def load_symbols_async():
            response = await send_request('get_symbols')
            if response['status'] == 'success':
                symbols = response['result']
                symbol_name.options = [dropdown.Option(symbol) for symbol in symbols]
                page.update()
            else:
                await show_alert(f"Error: {response['message']}")

        def load_symbols():
            asyncio.run_coroutine_threadsafe(load_symbols_async(), loop)

        async def load_account_info_async():
            response = await send_request('get_account_info')
            if response['status'] == 'success':
                account_info = response['result']
                balance_info.value = str(account_info['balance'])
                equity_info.value = str(account_info['equity'])
                margin_free_info.value = str(account_info['free_margin'])
                margin_level_info.value = str(account_info['margin_level'])
                page.update()
                await update_risk()
            else:
                await show_alert(f"Error: {response['message']}")

        def load_account_info():
            asyncio.run_coroutine_threadsafe(load_account_info_async(), loop)

        symbol_search.on_change = search_symbol
        symbol_name.on_change = symbol_changed
        risk_slider.on_change = update_risk_text
        order_action.on_change = toggle_entry_input
        open_order_switch.on_change = toggle_fill_policy
        initial_risk_input.on_change = lambda e: update_risk_slider()
        max_risk_input.on_change = lambda e: update_risk_slider()

        page.add(
            ResponsiveRow([
                Column([
                    Container(
                        content=Column([
                            summary_row,
                            Row([initial_risk_input, max_risk_input, daily_target_input, total_today_profit]),
                            Row([symbol_search, symbol_name]),
                            spread_text,
                            Row([risk_slider, risk_text]),
                            Row([order_action, entry_input]),
                            Row([stop_type]),
                            Row([stop_loss_input, profit_dropdown]),
                            Row([open_order_switch]),
                            Row([fill_policy]),
                            Row([buy_button, sell_button]),

                            result_text,
                            trades_list_view,

                        ]),
                        expand=1,
                        padding=10,
                    ),
                ]),
            ])
        )

        load_symbols()
        load_account_info()
        update_risk_slider()

        asyncio.run_coroutine_threadsafe(update_live_prices(), loop)
        asyncio.run_coroutine_threadsafe(update_account_info_async(), loop)


    init_database()

    config = get_server_config()
    if config:
        server_address, server_port = config
        initialize_app()
    else:
        show_server_config_dialog()

app(main)