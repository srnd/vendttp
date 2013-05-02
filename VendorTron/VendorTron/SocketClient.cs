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
        Inventory currentInventory;

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
                this.currentInventory = new Inventory();

                while (reader.ReadToFollowing("category"))
                {

                    Category c = new Category(reader.GetAttribute("name"));

                    reader.ReadToFollowing("item");
                    do
                        c.addItem(new Item(int.Parse(reader.GetAttribute("vendId")), decimal.Parse(reader.GetAttribute("price")), int.Parse(reader.GetAttribute("quantity")), reader.GetAttribute("name")));
                    while (reader.ReadToNextSibling("item"));

                    this.currentInventory.add(c);
                }

                HandleInventory(this.currentInventory);
            }
            else if (type == "balanceUpdate")
            {
                reader.ReadToFollowing("balance");
                HandleBalance((Decimal)reader.ReadElementContentAs(typeof(System.Decimal), null));
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
            Thread.Sleep(5);
            do
            {
                for (int i = 0; i < 10 && (client == null || !client.Connected); ++i) // try to connect to host 10 times
                    client = new TcpClient(host, PORT);

                if (!client.Connected)
                    return false;

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

        public bool buy(int id)
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
                                item.quantity--;
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

        public void logout()
        {
            Send("logout");
            currentBalance = -1;
            currentInventory = null;
        }

        private void Listen()
        {
            is_running = true;
            while (is_running)
            {
                Byte[] data = new Byte[2048];
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
