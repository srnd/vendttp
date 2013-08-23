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

namespace VendorTron
{
    public class Response
    {
        public String type;
        public String username;
        public Inventory inventory;
        public Decimal balance;
        public String reason;
        public String vendId;
    }
}
