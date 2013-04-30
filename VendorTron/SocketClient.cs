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

        Action<String> HandleMessage;
        Action HandleDisconnect;

        public void OnMessage(Action<String> HandleMessage)
        {
            this.HandleMessage = HandleMessage;
        }

        public void OnDisconnect(Action HandleDisconnect)
        {
            this.HandleDisconnect = HandleDisconnect;
        }

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

        public void Send(String message)
        {
            if (is_connected)
            {
                Byte[] data = System.Text.Encoding.UTF8.GetBytes(message);
                stream.Write(data, 0, data.Length);
            }

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
                else if (HandleMessage != null)
                    HandleMessage(responseData);
            }
        }
    }
}
