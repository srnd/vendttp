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

namespace Vendortron
{
    public partial class MainPage : PhoneApplicationPage
    {


        SocketClient client;

        // Constructor
        public MainPage()
        {
            InitializeComponent();

            client = new SocketClient();
            client.OnLogin(login);
            client.OnBalance(updateBalance);
            client.OnInventory(inventory);
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

        private void login(string name, decimal balance)
        {
            Dispatcher.BeginInvoke(() => CurrentUserBox.Text = name);

            Dispatcher.BeginInvoke(() => logoutButton.IsEnabled = true);

            updateBalance(balance);
        }

        private void updateBalance(decimal balance)
        {
            Dispatcher.BeginInvoke(() => balanceBox.Text = balance.ToString("C2"));
            Dispatcher.BeginInvoke(() => balanceBox.Visibility = Visibility.Visible);
        }

        private void inventory(Inventory inventory)
        {

        }

        private void OnDisconnect()
        {
            Dispatcher.BeginInvoke(() => balanceBox.Visibility = Visibility.Collapsed);
            Dispatcher.BeginInvoke(() => CurrentUserBox.Visibility = Visibility.Collapsed);
            Dispatcher.BeginInvoke(() => hostBox.Visibility = Visibility.Visible);
            Dispatcher.BeginInvoke(() => logoutButton.Content = "Connect");
            Dispatcher.BeginInvoke(() => logoutButton.IsEnabled = true);
        }

        private void logout_Click(object sender, RoutedEventArgs e)
        {
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
