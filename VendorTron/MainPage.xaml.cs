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
using SocketEx;


namespace Vendortron
{
    public partial class MainPage : PhoneApplicationPage
    {
        // Constants
        const int PORT = 8636;

        TcpClient client;
        Thread thread;
        Listener listener;
        Stream stream;

        // Constructor
        public MainPage()
        {
            InitializeComponent();

        }

        #region Body
        /// <summary>
        /// Handle the btnEcho_Click event by sending text to the echo server 
        /// and outputting the response
        /// </summary>
        private void btnEcho_Click(object sender, RoutedEventArgs e)
        {
            if (stream != null)
            {
                if (ValidateInput())
                {
                    LocalLog(">> " + SendTextBox.Text);
                    LocalLog(Environment.NewLine);
                    Byte[] data = System.Text.Encoding.UTF8.GetBytes(SendTextBox.Text);
                    stream.Write(data, 0, data.Length);
                    SendTextBox.Text = "";
                }
            }
            else
            {
                MessageBox.Show("Please connect to the server");
            }
        }

        private void btnConnect_Click(object sender, RoutedEventArgs args)
        {
            if (ValidateRemoteHost())
            {
                if (listener != null) listener.Stop();
                if (stream != null) stream.Close();
                if (client != null) client.Dispose();
                LocalLog("Connecting ... ");
                try
                {
                    client = new TcpClient(Host.Text, 8636);
                }
                catch (Exception e)
                {
                    LocalLog(Environment.NewLine);
                    LocalLog("Exception caught: " + e);
                    LocalLog(Environment.NewLine);
                    return;
                }
                stream = client.GetStream();
                listener = new Listener(stream, Log);
                thread = new Thread(new ThreadStart(listener.Listen));
                thread.Start();
                LocalLog(client.Connected ? "Success" : "Failure");
                LocalLog(Environment.NewLine);
            }
        }


        #region UI Validation
        /// <summary>
        /// Validates the txtInput TextBox
        /// </summary>
        /// <returns>True if the txtInput TextBox contains valid data, otherwise 
        /// False.
        ///</returns>
        private bool ValidateInput()
        {
            // txtInput must contain some text
            if (String.IsNullOrWhiteSpace(SendTextBox.Text))
            {
                MessageBox.Show("Please enter some text to send");
                return false;
            }

            return true;
        }

        /// <summary>
        /// Validates the txtRemoteHost TextBox
        /// </summary>
        /// <returns>True if the txtRemoteHost contains valid data,
        /// otherwise False
        /// </returns>
        private bool ValidateRemoteHost()
        {
            // The txtRemoteHost must contain some text
            if (String.IsNullOrWhiteSpace(Host.Text))
            {
                MessageBox.Show("Please enter a host name");
                return false;
            }

            return true;
        }
        #endregion

        #region Logging
        public void LocalLog(string message)
        {
            MainTextBox.Text += message;
        }

        public void Log(string message)
        {
            Dispatcher.BeginInvoke(() => MainTextBox.Text += "<< " + message + Environment.NewLine);
        }

        /// <summary>
        /// Clears the txtOutput TextBox
        /// </summary>
        private void ClearLog()
        {
            MainTextBox.Text = String.Empty;
        }
        #endregion

        #endregion
    }
}