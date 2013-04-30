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


namespace Vendortron {
    public partial class MainPage : PhoneApplicationPage {


        SocketClient client;

        // Constructor
        public MainPage() {
            InitializeComponent();

            client = new SocketClient();
            client.OnMessage(MessageFromServer);
            client.OnDisconnect(OnDisconnect);
        }

        private void Connect(string host)
        {
            client.Connect(host, setFields);
        }

        private void setFields()
        {
            client.Send("logout");
            Dispatcher.BeginInvoke(() => CurrentUserBox.Visibility = Visibility.Visible);
            Dispatcher.BeginInvoke(() => CurrentUserBox.Text = "No Login");
            Dispatcher.BeginInvoke(() => hostBox.Visibility = Visibility.Collapsed);
            Dispatcher.BeginInvoke(() => logoutButton.Content = "Logout");
            Dispatcher.BeginInvoke(() => logoutButton.IsEnabled = false);
        }

        private void MessageFromServer(string message) {

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
                Dispatcher.BeginInvoke(() => balanceBox.Text = "$" + balance.ToString());

                Dispatcher.BeginInvoke(() => balanceBox.Visibility = Visibility.Visible);
                Dispatcher.BeginInvoke(() => logoutButton.IsEnabled = true);
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
                Dispatcher.BeginInvoke(() => balanceBox.Text = "$" + balance.ToString());
            }
            
        }

        private void OnDisconnect() {
            Dispatcher.BeginInvoke(() => balanceBox.Visibility = Visibility.Collapsed);
            Dispatcher.BeginInvoke(() => CurrentUserBox.Visibility = Visibility.Collapsed);
            Dispatcher.BeginInvoke(() => hostBox.Visibility = Visibility.Visible);
            Dispatcher.BeginInvoke(() => logoutButton.Content = "Connect");
            Dispatcher.BeginInvoke(() => logoutButton.IsEnabled = true);
        }

        private void logout_Click(object sender, RoutedEventArgs e) {
            if (client.IsConnected())
            {
                setFields();
            }
            else
            {
                Connect(hostBox.Text);
            }
        }

    }
}
