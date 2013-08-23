using System;
using System.Net;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Documents;
using System.Windows.Ink;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Animation;
using System.Windows.Shapes;
using System.ComponentModel;

namespace VendorTron
{
    public class Item : INotifyPropertyChanged
    {
        public String vendId { get; private set; }
        public int quantity { get; private set; }
        public decimal price { get; private set; }
        public String name { get; private set; }
        public String info { get; private set; }
        public String Info
        {
            get { return info; }
            set { info = value; }
        }
        public Boolean Enabled
        {
            get { return quantity > 0; }
        }

        public Item(String vendId, decimal price, int quantity, String name)
        {
            this.vendId = vendId;
            this.price = price;
            this.quantity = quantity;
            this.name = name;
            this.Info = this.price.ToString("C2");
            UpdateInfo();
        }

        private void UpdateInfo()
        {
            if (this.quantity == 0)
            {
                this.Info = "SOLD OUT";
                NotifyPropertyChanged("Info");
                NotifyPropertyChanged("Enabled");
            }
        }

        public void decrement()
        {
            this.quantity--;
            this.UpdateInfo();
        }

        public void increment()
        {
            this.quantity++;
            this.UpdateInfo();
        }

        #region INotifiedProperty Block
        public event PropertyChangedEventHandler PropertyChanged;

        // This method is called by the Set accessor of each property. 
        // The CallerMemberName attribute that is applied to the optional propertyName 
        // parameter causes the property name of the caller to be substituted as an argument. 
        private void NotifyPropertyChanged(String propertyName)
        {
            if (PropertyChanged != null)
            {
                PropertyChanged(this, new PropertyChangedEventArgs(propertyName));
            }
        }
        #endregion
    }
}
