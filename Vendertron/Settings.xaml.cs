using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Navigation;
using Microsoft.Phone.Controls;
using Microsoft.Phone.Shell;
using System.IO.IsolatedStorage;

namespace Vendertron
{
    public partial class Settings : PhoneApplicationPage
    {
        #region Members

        

        #endregion

        public Settings()
        {
            InitializeComponent();

            string tmpserverip;
            if(IsolatedStorageSettings.ApplicationSettings.TryGetValue<string>("ServerIP", out tmpserverip)) IsolatedStorageSettings.ApplicationSettings.Add("ServerIP", "");
            ServerIP.Text = tmpserverip;
        }

        private void ServerIP_TextChanged(object sender, TextChangedEventArgs e)
        {
            string tmpserverip;
            if (IsolatedStorageSettings.ApplicationSettings.TryGetValue<string>("ServerIP", out tmpserverip)) IsolatedStorageSettings.ApplicationSettings["ServerIP"] = tmpserverip;
        }


    }
}