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
        const string HOST = "168.156.102.5";

        SocketClient client;

        // Constructor
        public MainPage() {
            InitializeComponent();

            client = new SocketClient();
            client.OnMessage(MessageFromServer);
            client.OnDisconnect(OnDisconnect);
            
        }

        private void Connect()
        {
            while(!client.IsConnected())
                client.Connect(HOST);
        }

        private void MessageFromServer(string message) {
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

        private void OnDisconnect() {
            Connect();
        }

        private void logout_Click(object sender, RoutedEventArgs e) {
            client.Send("logout");
            Dispatcher.BeginInvoke(() => CurrentUserBox.Text = "No Login");
        }

    }
}
