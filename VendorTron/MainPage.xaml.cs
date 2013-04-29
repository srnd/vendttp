using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Animation;
using System.Windows.Shapes;
using System.Windows.Threading;
using Microsoft.Phone.Controls;
using System.Threading;
using System.Text;
using System.IO;
using System.Xml;
using SocketEx;


namespace Vendortron {
    public partial class MainPage : PhoneApplicationPage {
        // Constants
        const int PORT = 8636;
        const string HOST = "168.156.102.5";

        TcpClient client;
        Thread thread;
        SocketClient listener;
        Stream stream;

        // Constructor
        public MainPage() {
            InitializeComponent();

            //Log("Connecting...");
            try {
                client = new TcpClient(HOST, PORT);
            }
            catch (Exception e) {
                //Log(Environment.NewLine);
                //Log("Exception caught: " + e);
                //Log(Environment.NewLine);
                return;
            }
            stream = client.GetStream();
            listener = new SocketClient(stream, LogFromServer, OnDisconnect);
            thread = new Thread(new ThreadStart(listener.Listen));
            thread.Start();
            //Log(client.Connected ? "Success" : "Failure");
            //Log(Environment.NewLine);
            
        }

        #region Body

 /*       private void btnConnect_Click(object sender, RoutedEventArgs args) {
            if (ValidateRemoteHost()) {
                if (listener != null) listener.Stop();
                if (stream != null) stream.Close();
                if (client != null) client.Dispose();
                Log("Connecting ... ");
                try {
                    client = new TcpClient(Host.Text, 8636);
                }
                catch (Exception e) {
                    Log(Environment.NewLine);
                    Log("Exception caught: " + e);
                    Log(Environment.NewLine);
                    return;
                }
                stream = client.GetStream();
                listener = new SocketClient(stream, LogFromServer, OnDisconnect);
                thread = new Thread(new ThreadStart(listener.Listen));
                thread.Start();
                Log(client.Connected ? "Success" : "Failure");
                Log(Environment.NewLine);
            }
        } */

        #region Logging
        private void LogFromServer(string message) {
            //Log("<< " + message + Environment.NewLine);

            XmlReader reader = XmlReader.Create(new StringReader(message));

            reader.ReadToFollowing("response");
            reader.MoveToAttribute("type");
            if (reader.Value == "account") {
                reader.ReadToFollowing("account");

                reader.MoveToAttribute("name");
                string name = reader.Value;
                Dispatcher.BeginInvoke(() => CurrentUserBox.Text = name);

                reader.MoveToAttribute("balance");
                float balance = float.Parse(reader.Value);
                Dispatcher.BeginInvoke(() => balanceBox.Text = balance.ToString());
            }
            else if (reader.Value == "inventory") {

                while (reader.MoveToAttribute("item")) {
                    while (reader.ReadToFollowing("item")) {

                    }
                }
            }
            else if (reader.Value == "balanceUpdate") {
                reader.ReadToFollowing("balance");
                float balance = reader.ReadElementContentAsFloat();
                Dispatcher.BeginInvoke(() => balanceBox.Text = balance.ToString());
            }
            
        }

/*        private void Log(string message) {
            Dispatcher.BeginInvoke(() => MainTextBox.Text += message);
        }

        private void ClearLog() {
            Dispatcher.BeginInvoke(() => MainTextBox.Text = String.Empty);
        } */

        private void OnDisconnect() {
            //Log("Disconnected" + Environment.NewLine);
            if (stream != null) stream.Close();
            stream = null;
            if (client != null) client.Dispose();
        }

        #endregion

        private void logout_Click(object sender, RoutedEventArgs e) {
            Byte[] data = System.Text.Encoding.UTF8.GetBytes("logout");
            stream.Write(data, 0, data.Length);
            Dispatcher.BeginInvoke(() => CurrentUserBox.Text = "No Login");
        }

        #endregion
    }
}
