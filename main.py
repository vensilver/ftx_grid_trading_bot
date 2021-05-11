# coding=utf-8
import datetime
import time
import simplejson as json
import ftx

COLOR_RESET = "\033[0;0m"
COLOR_GREEN = "\033[0;32m"
COLOR_RED = "\033[1;31m"
COLOR_BLUE = "\033[1;34m"
COLOR_WHITE = "\033[1;37m"
LOGFILE = ""


class Order_Info:
    def __init__(self):
        self.done = False
        self.side = None
        self.id = 0


class Grid_trader:
    def __init__(
        self, client, symbol, grid_level=0, lower_price=0.0, upper_price=0.0, amount=0
    ):
        self.symbol = symbol
        self.client = client
        market_info = self.client.get_market(self.symbol)
        self.price_increment = market_info["priceIncrement"]
        self.size_increment = market_info["sizeIncrement"]
        self.ask_price = market_info["ask"]
        self.last = market_info["last"]
        self.bid_price = market_info["bid"]
        self.grid_level = grid_level
        self.upper_price = upper_price
        self.lower_price = lower_price
        self.amount = amount
        self.interval_profit = (self.upper_price - self.lower_price) / self.grid_level
        self.order_list = []

    def place_order_init(self):
        # start cal level and place grid oreder
        last_price_grid_index = (self.last - self.lower_price) // self.interval_profit
        grid_index_with_order = sorted(list(range(self.grid_level + 1)), key=lambda x: abs(x-last_price_grid_index))
        for i in grid_index_with_order:  #  n+1 lines make n grid
            price = self.lower_price + i * self.interval_profit
            order = Order_Info()
            try:
                if price < self.last:
                    order.id = self.client.place_order(market=self.symbol, side="buy", price=price, size=self.amount, post_only=True)['id']
                    log("place buy order id = " + str(order.id) + " in " + str(price))
                else:
                    order.id = self.client.place_order(market=self.symbol, side="sell", price=price, size=self.amount, post_only=True)['id']
                    log("place sell order id = " + str(order.id) + " in " + str(price))
                self.order_list.append(order)
            except:
                # Todo fixed this issue
                log("update last price")
                market_info = self.client.get_market(self.symbol)
                self.last = market_info["last"]

    def loop_job(self):
        fill_history = client.get_fills()
        fill_history_dict = {o["orderId"]: o for o in fill_history}
        for order in self.order_list:
            order_info = fill_history_dict.get(order.id)
            # print(f"order.id: {order.id}")
            if order_info:
                side = order_info["side"]
                old_order_id = order_info["orderId"]
                msg = (
                    side
                    + " order id : "
                    + str(old_order_id)
                    + " : "
                    + str(order_info["price"])
                    + " completed , put "
                )
                if side == "buy":
                    new_order_price = float(order_info["price"]) + self.interval_profit
                    order.id = self.client.place_order(market=self.symbol, side="sell", price=new_order_price, size=self.amount, post_only=True)['id']
                    msg = msg + "sell"
                    log(msg)
                else:
                    new_order_price = float(order_info["price"]) - self.interval_profit
                    order.id = self.client.place_order(market=self.symbol, side="buy", price=new_order_price, size=self.amount, post_only=True)['id']
                    msg = msg + "buy"
                msg = (
                    msg + " order id : " + str(order.id) + " : " + str(new_order_price)
                )
                log(msg)
                self.order_list.append(order.id)


def log(msg):
    timestamp = datetime.datetime.now().strftime("%b %d %Y %H:%M:%S ")
    s = "[%s] %s:%s %s" % (timestamp, COLOR_WHITE, COLOR_RESET, msg)
    print(s)
    try:
        f = open(LOGFILE, "a")
        f.write(s + "\n")
        f.close()
    except:
        pass


def read_setting():
    with open("setting.json") as json_file:
        return json.load(json_file)


config = read_setting()
LOGFILE = config["LOGFILE"]


client = ftx.FtxClient(
    api_key=config["apiKey"],
    api_secret=config["secret"],
    subaccount_name=config["sub_account"],
)

main_job = Grid_trader(
    client,
    config["symbol"],
    config["grid_level"],
    config["lower_price"],
    config["upper_price"],
    config["amount"],
)
main_job.place_order_init()
while True:
    try:
        print(f"Loop in: {datetime.datetime.now()}, order list size {len(main_job.order_list)}")
        main_job.loop_job()
        time.sleep(1)
    except:
        time.sleep(1)

