import ccxt
import random
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from threading import Thread, Event
from time import sleep


app = FastAPI()

templates = Jinja2Templates(directory="templates")

thread_list = []

api_list = []


data_array = []
# class thread


class MyThread(Thread):
    def __init__(self,  min_val, max_val, interval_val, symbol_val, api_key, secret_key, password, exchange):
        super().__init__()

        self.min_val = min_val
        self.max_val = max_val
        self.interval_val = interval_val
        self.symbol_val = symbol_val
        self.api_key = api_key
        self.secret_key = secret_key
        self.password = password
        self.exchange = exchange
        self.th_index = len(thread_list)
        self._stop_event = Event()

    def stop(self):
        self._stop_event.set()

    def run(self):
        while not self._stop_event.is_set():
            global data_array, api_list, thread_list
            try:
                e_rate = self.exchange.fetch_ticker(self.symbol_val)
                rand_amount = random.randint(self.min_val, self.max_val)
                sell_amount = rand_amount / e_rate['close']

                self.exchange.create_order(
                    self.symbol_val, 'market', 'sell', sell_amount)

                balance = self.exchange.fetch_balance()

                remaining_eth = balance[self.symbol_val.split("/")[0]]['free']

                data_array[self.th_index]["remain"] = remaining_eth

                print("Remaining ETH", self.th_index, ":", remaining_eth)
            except:
                data_array.pop(self.th_index)
                api_list.pop(self.th_index)
                thread_list.pop(self.th_index)
                self._stop_event.set()

                print("error occured")
                return

            sleep(self.interval_val)

# Model for information


class Item(BaseModel):
    api_key: str
    secret_key: str
    api_password: str
    min_val: int
    max_val: int
    interval_time: int
    marketing_symbol: str


@app.get("/")
async def init_view(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/getremain")
async def init_message():

    return data_array


@app.get("/stop")
async def stop_sell():
    global data_array, api_list, thread_list
    try:
        for c in thread_list:
            c.stop()
        thread_list.clear()
        api_list.clear()
        data_array.clear()
        return "success"
    except:
        return "failed"


@app.post("/register")
async def startdata(item: Item):
    exchange = ccxt.kucoin({
        'apiKey': item.api_key,
        'secret': item.secret_key,
        'password': item.api_password,
        'enableRateLimit': True,
    })

    # exchange.set_sandbox_mode(True)

    try:

        if item.api_key in api_list:
            return "repeat"
        exchange.fetch_ticker(item.marketing_symbol)
        t = MyThread(min_val=item.min_val, max_val=item.max_val,
                     interval_val=item.interval_time, symbol_val=item.marketing_symbol,
                     api_key=item.api_key, secret_key=item.secret_key,
                     password=item.api_password, exchange=exchange)
        t.start()
        global data_array, thread_list, api_list
        data_array.append({"min_val": item.min_val, "max_val": item.max_val,
                          "interval_time": item.interval_time, "market_symbol": item.marketing_symbol, "remain": 0, "status": "progressive"})
        thread_list.append(t)
        api_list.append(item.api_key)

        return "success"
    except:
        return "failed"
