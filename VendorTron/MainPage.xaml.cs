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
            Dispatcher.BeginInvoke(() => logoutButton.IsEnabled = false);
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
            foreach (Category category in inventory.categories)
            {

                Dispatcher.BeginInvoke(() =>
                {
                    Grid grid = new Grid();

                    /*StreamResourceInfo image = Application.GetResourceStream(new Uri("Tile.png", UriKind.Relative));
                    WriteableBitmap bmp = new WriteableBitmap(1, 1);
                    bmp.SetSource(image.Stream); */

                    TextBlock text = new TextBlock() { FontSize = (double)Resources["PhoneFontSizeLarge"], Foreground = new SolidColorBrush(Colors.White) };
                    text.Text = category.name + "\n";

                    Rectangle rect = new Rectangle();
                    rect.Width = 150;
                    rect.Height = 150;

                    grid.Children.Add(rect);
                    grid.Children.Add(text);

                    grid.Width = 200;
                    grid.Height = 200;
                    grid.Background = new SolidColorBrush(Colors.Blue);

                    inventoryGrid.Children.Add(grid);
                });


                /*Rectangle rect = new Rectangle();
                rect.Height = 150;
                rect.Width = 250;
                inventoryGrid.Children.Add(rect); */
            }

        }

        private void OnDisconnect()
        {
            Dispatcher.BeginInvoke(() => balanceBox.Visibility = Visibility.Collapsed);
            Dispatcher.BeginInvoke(() => CurrentUserBox.Visibility = Visibility.Collapsed);
            Dispatcher.BeginInvoke(() => hostBox.Visibility = Visibility.Visible);
            Dispatcher.BeginInvoke(() => logoutButton.Content = "Connect");
            Dispatcher.BeginInvoke(() => logoutButton.IsEnabled = true);
        }

        #endregion

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
