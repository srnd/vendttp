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
using System.Windows.Resources;
using System.Windows.Media.Imaging;
using System.IO.IsolatedStorage;

namespace Vendortron
{
    public partial class MainPage : PhoneApplicationPage
    {

        Boolean disconnect = false;
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
            client.OnLogout(onLogout);

            string tmpserverip;
            if(IsolatedStorageSettings.ApplicationSettings.TryGetValue<string>("ServerIP", out tmpserverip))
                hostBox.Text = tmpserverip;
        }

        private void Connect(string host)
        {
            client.Connect(host, onConnect);
        }

        private void onConnect() {
            IsolatedStorageSettings.ApplicationSettings["ServerIP"] = hostBox.Text;

            waitView();
        }

        private void onLogout()
        {
            waitView();
        }

        private void waitView()
        {   Dispatcher.BeginInvoke(() =>
            {   CurrentUserBox.Text = "No Login";
                CurrentUserBox.Visibility = Visibility.Visible;
                logoutButton.Visibility = Visibility.Visible;
                logoutButton.IsEnabled = false;
                hostBox.Visibility = Visibility.Collapsed;
                connectButton.Visibility = Visibility.Collapsed;
                itemList.Visibility = Visibility.Collapsed;
                categoryList.Visibility = Visibility.Collapsed;
                balanceBox.Visibility = Visibility.Collapsed;
                numpad.Visibility = Visibility.Collapsed;
                backButton.Visibility = Visibility.Collapsed;
                numpadButton.Visibility = Visibility.Collapsed;
                enteredNumbers.Visibility = Visibility.Collapsed;
                balanceBox.Visibility = Visibility.Collapsed;
                if (disconnect) disconnectButton.Visibility = Visibility.Visible;
            });
        }

        private void inventoryView()
        {   Dispatcher.BeginInvoke(() =>
            {   categoryList.Visibility = Visibility.Visible;
                itemList.Visibility = Visibility.Collapsed;
                balanceBox.Visibility = Visibility.Visible;
                numpad.Visibility = Visibility.Collapsed;
                backButton.Visibility = Visibility.Collapsed;
                numpadButton.Visibility = Visibility.Visible;
                enteredNumbers.Visibility = Visibility.Collapsed;
                balanceBox.Visibility = Visibility.Visible;
                disconnectButton.Visibility = Visibility.Collapsed;
            });
        }

        private void numpadView()
        {   Dispatcher.BeginInvoke(() =>
            {   categoryList.Visibility = Visibility.Collapsed;
                itemList.Visibility = Visibility.Collapsed;
                balanceBox.Visibility = Visibility.Visible;
                numpad.Visibility = Visibility.Visible;
                backButton.Visibility = Visibility.Visible;
                numpadButton.Visibility = Visibility.Collapsed;
                enteredNumbers.Visibility = Visibility.Visible;
                balanceBox.Visibility = Visibility.Visible;
            });
        }

        private void hostView()
        {
            Dispatcher.BeginInvoke(() =>
            {
                CurrentUserBox.Visibility = Visibility.Collapsed;
                logoutButton.Visibility = Visibility.Collapsed;
                hostBox.Visibility = Visibility.Visible;
                connectButton.Visibility = Visibility.Visible;
                itemList.Visibility = Visibility.Collapsed;
                categoryList.Visibility = Visibility.Collapsed;
                balanceBox.Visibility = Visibility.Collapsed;
                numpad.Visibility = Visibility.Collapsed;
                backButton.Visibility = Visibility.Collapsed;
                numpadButton.Visibility = Visibility.Collapsed;
                enteredNumbers.Visibility = Visibility.Collapsed;
                balanceBox.Visibility = Visibility.Collapsed;
                disconnectButton.Visibility = Visibility.Collapsed;
            });
        }

        private void login(string name, decimal balance)
        {
            Dispatcher.BeginInvoke(() =>
            {
                CurrentUserBox.Text = name;
                logoutButton.IsEnabled = true;
            });

            updateBalance(balance);
        }

        private void updateBalance(decimal balance)
        {
            Dispatcher.BeginInvoke(() =>
            {
                balanceBox.Text = balance.ToString("C2");
                balanceBox.Visibility = Visibility.Visible;
            });
        }

        private void inventory(Inventory inventory)
        {
            Dispatcher.BeginInvoke(() =>
            {
                //Scroll to top???
                categoryList.ItemsSource = inventory.categories;
                inventoryView();
            });
        }

        private void category_Click(object sender, RoutedEventArgs e)
        {
            Button source = e.OriginalSource as Button;
            Category category = source.DataContext as Category;

            if (category == null || category.items == null || category.items.Count == 0)
                return;

            Dispatcher.BeginInvoke(() =>
            {
                categoryList.Visibility = Visibility.Collapsed;

                itemList.ItemsSource = category.items;

                itemList.Visibility = Visibility.Visible;
                backButton.Visibility = Visibility.Visible;
            });
            client.Touch();
        }

        private void item_Click(object sender, RoutedEventArgs e)
        {
            Button source = e.OriginalSource as Button;
            Item item = source.DataContext as Item;

            if (item == null)
                return;

            client.buy(item);

            inventoryView();
            client.Touch();
        }

        private void OnDisconnect()
        {
            hostView();
        }

        private void connect_Click(object sender, RoutedEventArgs e)
        {
            Connect(hostBox.Text);
        }

        private void logout_Click(object sender, RoutedEventArgs e)
        {
            client.logout();
        }

        private void back_Click(object sender, RoutedEventArgs e) {
            inventoryView();
            client.Touch();
        }

        private void numpadButton_Click(object sender, RoutedEventArgs e)
        {
            numpadView();
            client.Touch();
        }

        private void numpad_Click(object sender, RoutedEventArgs e)
        {
            Button b = (Button)sender;
            String enteredText = (String)enteredNumbers.Content;
            if (enteredText.Length < 2)
            {
                if (enteredText.Length == 1)
                {
                    Dispatcher.BeginInvoke(() =>
                    {
                        sendButton.Background = new SolidColorBrush(Colors.Black);
                        sendButton.IsEnabled = true;
                    });
                }
                Dispatcher.BeginInvoke(() =>
                {
                    enteredNumbers.Content = enteredText + (String)b.Content;
                });
            }
            client.Touch();
        }

        private void delete_Click(object sender, RoutedEventArgs e)
        {
            String enteredText = (String)enteredNumbers.Content;
            if (enteredText.Length > 0)
            {
                Dispatcher.BeginInvoke(() =>
                {
                    enteredNumbers.Content = enteredText.Substring(0, enteredText.Length - 1);
                    sendButton.IsEnabled = false;
                    sendButton.Background = new SolidColorBrush(Colors.Red);
                });
            }
            client.Touch();
        }

        private void send_Click(object sender, RoutedEventArgs e)
        {
            bool b = client.buy((String) enteredNumbers.Content);
            if (b)
            {
                Dispatcher.BeginInvoke(() =>
                {
                    enteredNumbers.Content = "";
                });
            }
        }

        private void disconnect_Click(object sender, RoutedEventArgs e)
        {
            client.Disconnect();
        }

        private void MainPanel_MouseEnter(object sender, MouseEventArgs e)
        {
            client.Touch();
        }

        private void MainPanel_MouseLeave(object sender, MouseEventArgs e)
        {
            client.Touch();
        }

    }
}
