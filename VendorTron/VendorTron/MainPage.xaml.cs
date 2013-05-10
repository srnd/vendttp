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

            setFields();
        }

        private void setFields()
        {
            Dispatcher.BeginInvoke(() =>
            {
                CurrentUserBox.Text = "No Login";
                CurrentUserBox.Visibility = Visibility.Visible;
                hostBox.Visibility = Visibility.Collapsed;
                logoutButton.Content = "Logout";
                logoutButton.Click -= connect_Click;
                logoutButton.Click += logout_Click;
                logoutButton.IsEnabled = false;
                balanceBox.Visibility = Visibility.Collapsed;
                itemList.Visibility = Visibility.Collapsed;
                categoryList.Visibility = Visibility.Collapsed;
            });
        }

        #region handlers

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
                categoryList.ItemsSource = inventory.categories;
                itemList.Visibility = Visibility.Collapsed;
                categoryList.Visibility = Visibility.Visible;
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
                backButton.IsEnabled = true;
            });

        }

        private void item_Click(object sender, RoutedEventArgs e)
        {
            Button source = e.OriginalSource as Button;
            Item item = source.DataContext as Item;

            if (item == null)
                return;

            client.buy(item.vendId);
            item.quantity--;

            Dispatcher.BeginInvoke(() =>
            {
                categoryList.Visibility = Visibility.Visible;
                itemList.Visibility = Visibility.Collapsed;
                backButton.Visibility = Visibility.Collapsed;
                backButton.IsEnabled = false;
            });

        }

        private void OnDisconnect()
        {
            Dispatcher.BeginInvoke(() =>
            {
                balanceBox.Visibility = Visibility.Collapsed;
                CurrentUserBox.Visibility = Visibility.Collapsed;
                categoryList.Visibility = Visibility.Collapsed;
                itemList.Visibility = Visibility.Collapsed;
                hostBox.Visibility = Visibility.Visible;
                logoutButton.Content = "Connect";
                logoutButton.IsEnabled = true;
                logoutButton.Click += connect_Click;
                logoutButton.Click -= logout_Click;
            });
        }

        #endregion

        private void connect_Click(object sender, RoutedEventArgs e)
        {
            Connect(hostBox.Text);
        }

        private void logout_Click(object sender, RoutedEventArgs e)
        {
            Dispatcher.BeginInvoke(() => ((Button)sender).IsEnabled = false);
            client.logout();
            setFields();
        }

        private void back_Click(object sender, RoutedEventArgs e) {
            Dispatcher.BeginInvoke(() =>
            {
                categoryList.Visibility = Visibility.Visible;
                itemList.Visibility = Visibility.Collapsed;
                backButton.Visibility = Visibility.Collapsed;
                backButton.IsEnabled = false;
            });
        }

    }
}
