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
using System.Collections.Generic;
using SocketEx;
using Newtonsoft.Json;

namespace VendorTron
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

        Stopwatch stopwatch = new Stopwatch();

        public Boolean IsConnected() { return is_connected; }

        public Boolean AutomaticallyReconnect;

        public Decimal currentBalance;
        public Inventory storedInventory;

        #region handlers
        Action<String, Decimal> HandleLogin;
        Action<Decimal> HandleBalance;
        Action<Inventory> HandleInventory;
        Action HandleDisconnect;
        Action HandleLogout;

        public void OnLogin(Action<String, Decimal> HandleLogin)
        {
            this.HandleLogin = HandleLogin;
        }

        public void OnBalance(Action<Decimal> HandleBalance)
        {
            this.HandleBalance = HandleBalance;
        }

        public void OnDisconnect(Action HandleDisconnect)
        {
            this.HandleDisconnect = HandleDisconnect;
        }

        public void OnInventory(Action<Inventory> HandleInventory)
        {
            this.HandleInventory = HandleInventory;
        }

        public void OnLogout(Action HandleLogout)
        {
            this.HandleLogout = HandleLogout;
        }

        private void HandleMessage(string message)
        {
            Response response = JsonConvert.DeserializeObject<Response>(message);
            if (response.type == "log in")
            {
                Debug.WriteLine("received login");
                this.currentBalance = response.balance;
                HandleLogin(response.username, response.balance);
                Request request;
                if (storedInventory != null) request = Request.Inventory(storedInventory.key);
                else request = Request.Inventory();
                Send(request.ToJSON());
                Debug.WriteLine("handled login");
                Touch();
            }
            else if (response.type == "inventory")
            {
                Debug.WriteLine("received inventory");
                if (currentBalance < 0)
                    return;
                if (storedInventory != null && response.inventory.key == storedInventory.key)
                    HandleInventory(storedInventory);
                else
                {
                    Debug.WriteLine("new inventory");
                    storedInventory = response.inventory;
                    HandleInventory(storedInventory);
                    storedInventory.Index();
                }
                Debug.WriteLine("handled inventory");
                Touch();
            }
            else if (response.type == "balance update")
            {
                Debug.WriteLine("received balance update");
                currentBalance = response.balance;
                HandleBalance(response.balance);
                Touch();
            }
            else if (response.type == "vend success")
            {
                Debug.WriteLine("received vend success");
                currentBalance = response.balance;
                HandleBalance(response.balance);
            }
            else if (response.type == "vend failure")
            {
                Debug.WriteLine("received vend failure of type '" + response.reason + "'");
                storedInventory.FindItem(response.vendId).increment();
            }
            else
            {
                Debug.WriteLine("received erronious message of type '" + response.type + "'");
            }
        }


        #endregion

        #region socketstuff
        public Boolean Connect(String host, Action onConnect = null)
        {
            if (host == null || host.Length < 7 || host.Length > 15)
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

        public void buy(Item item)
        {
            if (item.quantity > 0 && item.price <= this.currentBalance)
            {
                Send(Request.Vend(item.vendId).ToJSON());
                item.decrement();
                Debug.WriteLine("item bought: " + item.vendId);
                Debug.WriteLine("  new qty: " + item.quantity);
                Debug.WriteLine("  new info: " + item.info);
            }
            else
                Debug.WriteLine("item not bought");
        }

        public void guest()
        {
            Send(Request.Guest().ToJSON());
            this.currentBalance = 0;
            HandleLogin("guest", 0);
            Request request;
            if (storedInventory != null) request = Request.Inventory(storedInventory.key);
            else request = Request.Inventory();
            Send(request.ToJSON());
            Touch();
        }

        public void logout()
        {
            if (currentBalance >= 0)
            {
                Send(Request.LogOut().ToJSON());
                currentBalance = -1;
                HandleLogout();
            }
            StopTimer();
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
                    HandleMessage(responseData);
                }
            }
        }
        #endregion
    }
}
