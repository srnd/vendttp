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
            client.logout();
            Dispatcher.BeginInvoke(() => CurrentUserBox.Visibility = Visibility.Visible);
            Dispatcher.BeginInvoke(() => CurrentUserBox.Text = "No Login");
            Dispatcher.BeginInvoke(() => hostBox.Visibility = Visibility.Collapsed);
            Dispatcher.BeginInvoke(() => logoutButton.Content = "Logout");
            logoutButton.Click -= connect_Click;
            logoutButton.Click += logout_Click;
            Dispatcher.BeginInvoke(() => logoutButton.IsEnabled = false);
            Dispatcher.BeginInvoke(() => balanceBox.Visibility = Visibility.Collapsed);
        }

        #region handlers

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

            Dispatcher.BeginInvoke(() => categoryList.ItemsSource = inventory.categories);
        }

        private void category_Click(object sender, RoutedEventArgs e)
        {
            Button source = e.OriginalSource as Button;
            Category category = source.DataContext as Category;

            if (category == null || category.items == null || category.items.Count == 0)
                return;

            Dispatcher.BeginInvoke(() => categoryList.Visibility = Visibility.Collapsed);

            Dispatcher.BeginInvoke(() => itemList.ItemsSource = category.items);

            Dispatcher.BeginInvoke(() => itemList.Visibility = Visibility.Visible);

        }

        private void item_Click(object sender, RoutedEventArgs e)
        {
            Button source = e.OriginalSource as Button;
            Item item = source.DataContext as Item;

            if (item == null)
                return;

            client.buy(item.vendId);
            item.quantity--;

            Dispatcher.BeginInvoke(() => categoryList.Visibility = Visibility.Visible);
            Dispatcher.BeginInvoke(() => itemList.Visibility = Visibility.Collapsed);

        }

        private void OnDisconnect()
        {
            Dispatcher.BeginInvoke(() => balanceBox.Visibility = Visibility.Collapsed);
            Dispatcher.BeginInvoke(() => CurrentUserBox.Visibility = Visibility.Collapsed);
            Dispatcher.BeginInvoke(() => hostBox.Visibility = Visibility.Visible);
            Dispatcher.BeginInvoke(() => logoutButton.Content = "Connect");
            logoutButton.Click += connect_Click;
            logoutButton.Click -= logout_Click;
            Dispatcher.BeginInvoke(() => logoutButton.IsEnabled = true);
        }

        #endregion

        private void connect_Click(object sender, RoutedEventArgs e)
        {
            Connect(hostBox.Text);
        }

        private void logout_Click(object sender, RoutedEventArgs e)
        {
            setFields();
        }

    }
}
