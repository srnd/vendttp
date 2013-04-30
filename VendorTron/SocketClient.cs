using System;
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
        Thread thread;
        Stream stream;
        Boolean is_running = true;
        Boolean is_connected = false;

        public Boolean IsConnected() { return is_connected; }

        public Boolean AutomaticallyReconnect;

        decimal currentBalance;
        
        #region handlers
        Action<String, decimal> HandleLogin;
        Action<decimal> HandleBalance;
        Action<Inventory> HandleInventory;
        Action HandleDisconnect;

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

        #endregion

        private void HandleMessage(string message)
        {
            XmlReader reader = XmlReader.Create(new StringReader(message));

            reader.ReadToFollowing("response");
            string type = reader.GetAttribute("type");
            if (type == "account")
            {
                reader.ReadToFollowing("account");

                decimal balance = decimal.Parse(reader.GetAttribute("balance"));

                this.currentBalance = balance;

                HandleLogin(reader.GetAttribute("name"), balance);
            }
            else if (type == "inventory")
            {
                Inventory inventory = new Inventory();

                while (reader.MoveToAttribute("category"))
                {
                    Category c = new Category(reader.GetAttribute("name"));

                    while (reader.ReadToFollowing("item"))
                        c.addItem(new Item(int.Parse(reader.GetAttribute("id")), int.Parse(reader.GetAttribute("vendId")), decimal.Parse(reader.GetAttribute("price")), int.Parse(reader.GetAttribute("quantity")), reader.GetAttribute("name")));

                    inventory.add(c);
                }

                HandleInventory(inventory);
            }
            else if (type == "balanceUpdate")
            {
                HandleBalance(decimal.Parse(reader.GetAttribute("balance")));
            }
        }

        #region socketstuff
        public Boolean Connect(String host, Action onConnect = null)
        {
            is_connected = false;
            is_running = false;
            if (stream != null) stream.Close();
            if (client != null) client.Dispose();
            Thread.Sleep(5);
            do
            {
                do
                    client = new TcpClient(host, PORT);
                while (!client.Connected);

                stream = client.GetStream();
                thread = new Thread(new ThreadStart(Listen));
                thread.Start();
                Thread.Sleep(5);
                is_connected = is_running;
            } while (!is_connected);

            if (onConnect != null)
                onConnect();
            return is_connected;
        }

        private void Send(String message)
        {
            if (is_connected)
            {
                Byte[] data = System.Text.Encoding.UTF8.GetBytes(message);
                stream.Write(data, 0, data.Length);
            }

        }

        public void buy(int id)
        {
            Send("i" + id);
        }

        public void logout()
        {
            Send("logout");
        }

        private void Listen()
        {
            is_running = true;
            while (is_running)
            {
                Byte[] data = new Byte[256];
                Int32 bytes = stream.Read(data, 0, data.Length);
                String responseData = System.Text.Encoding.UTF8.GetString(data, 0, bytes);
                if (responseData.Length == 0)
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
