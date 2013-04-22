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
using SocketEx;


namespace Vendertron
{
    class Listener
    {
        SocketClient client;
        Action<string> log;
        Dispatcher dispatcher;

        public Listener(SocketClient client, MainPage page)
        {
            this.client = client;
            this.log = page.Log;
            this.dispatcher = page.Dispatcher;
        }

        public void Listen()
        {
            while (true)
            {
                string s = client.Receive();
                if (s != null)
                {
                    dispatcher.BeginInvoke(() => log(s + Environment.NewLine));
                }
            }
        }
    }
    public partial class MainPage : PhoneApplicationPage
    {
        // Constants
        const int PORT = 8636;

        SocketClient client = new SocketClient();
        Thread thread;
        
        // Constructor
        public MainPage()
        {
            InitializeComponent();

        }

        #region Some Shit
        /// <summary>
        /// Handle the btnEcho_Click event by sending text to the echo server 
        /// and outputting the response
        /// </summary>
        private void btnEcho_Click(object sender, RoutedEventArgs e)
        {
            if (ValidateInput())
            {
                Log(">> " + SendTextBox.Text);
                Log(Environment.NewLine);
                client.Send(SendTextBox.Text);
                SendTextBox.Text = "";
            }
        }

        private void btnConnect_Click(object sender, RoutedEventArgs e)
        {
            if (ValidateRemoteHost())
            {
                if (thread != null) thread.Abort();
                client.Close();
                Log(">> Connecting ... ");
                var connected = client.Connect(Host.Text, 8636);
                Listener l = new Listener(client, this);
                thread = new Thread(new ThreadStart(l.Listen));
                thread.Start();
                Log(connected);
                Log(Environment.NewLine);
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
        /// <summary>
        /// Log text to the txtOutput TextBox
        /// </summary>
        /// <param name="message">The message to write to the txtOutput TextBox</param>
        /// <param name="isOutgoing">True if the message is an outgoing (client to server)
        /// message, False otherwise.
        /// </param>
        /// <remarks>We differentiate between a message from the client and server 
        /// by prepending each line  with ">>" and "<<" respectively.</remarks>
        public void Log(string message)
        {
            MainTextBox.Text += message;
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