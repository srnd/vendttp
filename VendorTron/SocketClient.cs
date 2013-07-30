using System;
using System.Diagnostics;
using System.Net;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Documents;
using System.Windows.Ink;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Animation;
using System.Windows.Shapes;
using System.Net.Sockets;
using System.IO;
using System.Threading;
using SocketEx;
using System.Xml;

namespace Vendortron
{
    public class SocketClient
    {
        const int PORT = 8636;

        TcpClient client;
        Thread listen_Thread;
        Thread timeout_Thread;
        Stream stream;
        Boolean is_running = true;
        Boolean is_connected = false;
        Boolean debug = true;

        Stopwatch stopwatch = new Stopwatch();

        public Boolean IsConnected() { return is_connected; }

        public Boolean AutomaticallyReconnect;

        decimal currentBalance;
        Inventory currentInventory;

        #region handlers
        Action<String, decimal> HandleLogin;
        Action<decimal> HandleBalance;
        Action<Inventory> HandleInventory;
        Action HandleDisconnect;
        Action HandleLogout;

        public void OnLogin(Action<String, decimal> Handle)
        {
            this.HandleLogin = Handle;
        }

        public void OnBalance(Action<decimal> Handle)
        {
            this.HandleBalance = Handle;
        }

        public void OnDisconnect(Action HandleDisconnect)
        {
            this.HandleDisconnect = HandleDisconnect;
        }

        public void OnInventory(Action<Inventory> Handle)
        {
            this.HandleInventory = Handle;
        }

        public void OnLogout(Action Handle)
        {
            this.HandleLogout = Handle;
        }

        private void HandleMessage(string message)
        {
            if (debug) Debug.WriteLine("received message: " + message);
            XmlReader reader = XmlReader.Create(new StringReader(message));
            reader.ReadToFollowing("response");
            string type = reader.GetAttribute("type");
            if (type == "account")
            {
                if (debug) Debug.WriteLine("received login");
                reader.ReadToFollowing("account");
                decimal balance = decimal.Parse(reader.GetAttribute("balance"));
                this.currentBalance = balance;
                if (debug) Debug.WriteLine("handling login");
                HandleLogin(reader.GetAttribute("name"), balance);
                Touch();
            }
            else if (type == "inventory")
            {   if (debug) Debug.WriteLine("received inventory");
                this.currentInventory = new Inventory();
                reader.ReadToFollowing("category");
                do
                {   Category c = new Category(reader.GetAttribute("name"));
                    reader.ReadToFollowing("item");
                    do
                    {   c.addItem(new Item(reader.GetAttribute("vendId"),
                                           decimal.Parse(reader.GetAttribute("price")),
                                           int.Parse(reader.GetAttribute("quantity")),
                                           reader.GetAttribute("name")));
                    }   while (reader.ReadToNextSibling("item"));
                    this.currentInventory.add(c);
                }   while (reader.ReadToNextSibling("category"));
                HandleInventory(this.currentInventory);
                Debug.WriteLine("handled inventory");
                Touch();
            }
            else if (type == "balanceUpdate")
            {   if (debug) Debug.WriteLine("receive balanceUpdate");
                reader.ReadToFollowing("balance");
                decimal balance = (Decimal)reader.ReadElementContentAs(typeof(System.Decimal), null);
                currentBalance = balance;
                if (debug) Debug.WriteLine("handling balanceUpdate");
                HandleBalance(balance);
                Touch();
            }
            else
            {
                Debug.WriteLine("received erronious message fo type `" + type + "`");
            }
        }


        #endregion

        #region socketstuff
        public Boolean Connect(String host, Action onConnect = null)
        {
            if (host == null || host.Length < "0.0.0.0".Length || host.Length > "000.000.000.000".Length)
                return false;

            is_connected = false;
            is_running = false;
            if (stream != null) stream.Close();
            if (client != null) client.Dispose();
            for (int i = 0; i < 10 && (client == null || !client.Connected); ++i) // try to connect to host 10 times
                client = new TcpClient(host, PORT);

            if (!client.Connected)
                return false;

            stream = client.GetStream();
            listen_Thread = new Thread(new ThreadStart(Listen));
            listen_Thread.Start();
            Thread.Sleep(1);

            timeout_Thread = new Thread(new ThreadStart(TimeLogout));
            timeout_Thread.Start();

            is_connected = is_running;

            if (is_connected && onConnect != null)
            {
                onConnect();
            }
            return is_connected;

        }

        public void Disconnect()
        {
            is_connected = false;
            is_running = false;
            if (stream != null) stream.Close();
            if (client != null) client.Dispose();
        }

        private void Send(String message)
        {
            if (is_connected)
            {
                Byte[] data = System.Text.Encoding.UTF8.GetBytes(message);
                stream.Write(data, 0, data.Length);
            }

        }

        public bool buy(String id)
        {
            if (currentInventory != null)
            {
                foreach (Category category in currentInventory.categories)
                {
                    foreach (Item item in category.items)
                    {
                        if (item.vendId == id)
                        {
                            if (item.quantity > 0 && item.price <= this.currentBalance)
                            {
                                item.decrement();
                                Send("i" + id);
                                return true;
                            }
                            else
                            {
                                return false;
                            }
                        }
                    }
                }
            }
            return false;
        }

        public bool buy(Item item)
        {
            if (item.quantity > 0 && item.price <= this.currentBalance)
            {
                item.decrement();
                Send("i" + item.vendId);
                return true;
            }
            else
            {
                return false;
            }
        }

        public void logout()
        {
            if (this.currentBalance >= 0)
            {
                Send("logout");
                this.currentBalance = -1;
                this.currentInventory = null;
                HandleLogout();
            }
            stopwatch.Stop();
        }

        public void Touch()
        {
            stopwatch.Reset();
            stopwatch.Start();
        }
        public void StopTimer()
        {
            stopwatch.Reset();
        }
        public void StartTimer()
        {
            stopwatch.Start();
        }

        private void TimeLogout()
        {
            while (true)
            {
                if (stopwatch.IsRunning && stopwatch.ElapsedMilliseconds > 30000)
                {
                        logout();
                }
                Thread.Sleep(2000);
            }
        }

        private void Listen()
        {
            is_running = true;
            while (is_running)
            {
                StreamReader reader = new StreamReader(stream);
                String responseData = reader.ReadLine();
                if (responseData == null || responseData.Length == 0)
                {
                    if (HandleDisconnect != null) HandleDisconnect();
                    is_running = false;
                }
                else
                {
                    Debug.WriteLine(responseData);
                    HandleMessage(responseData);
                }
            }
        }
        #endregion
    }
}
