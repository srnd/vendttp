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
            Debug.WriteLine(message.Length);
            if (debug) Debug.WriteLine("received message: " + message);
            Response response = JsonConvert.DeserializeObject<Response>(message);
            if (response.type == "log in")
            {
                if (debug) Debug.WriteLine("received login");
                this.currentBalance = response.balance;
                HandleLogin(response.username, response.balance);
                this.currentInventory = new Inventory(response.inventory);
                HandleInventory(this.currentInventory);
                this.currentInventory.Index();
                if (debug) Debug.WriteLine("handled login");
                Touch();
            }
            else if (response.type == "balance")
            {   if (debug) Debug.WriteLine("received balance update");
                currentBalance = response.balance;
                HandleBalance(response.balance);
                Touch();
            }
            else if (response.type == "vend success")
            {
                if (debug) Debug.WriteLine("received vend success");
                currentBalance = response.balance;
                HandleBalance(response.balance);
            }
            else if (response.type == "vend failure")
            {
                if (debug) Debug.WriteLine("received vend failure of type '" + response.reason + "'");
            }
            else
            {
                if (debug) Debug.WriteLine("received erronious message of type '" + response.type + "'");
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

        public bool buy(String vendId)
        {
            if (debug) Debug.WriteLine("buy(" + vendId + ")");
            if (currentInventory != null)
            {
                Item item = currentInventory.FindItem(vendId);
                if (item == null) return false;
                return buy(item);
            }
            return false;
        }

        public bool buy(Item item)
        {
            if (item.quantity > 0 && item.price <= this.currentBalance)
            {
                Send(JsonConvert.SerializeObject(Request.Vend(item.vendId)));
                return true;
            }
            else return false;
        }

        public void logout()
        {
            if (this.currentBalance >= 0)
            {
                Send(JsonConvert.SerializeObject(Request.LogOut()));
                this.currentBalance = -1;
                this.currentInventory = null;
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
