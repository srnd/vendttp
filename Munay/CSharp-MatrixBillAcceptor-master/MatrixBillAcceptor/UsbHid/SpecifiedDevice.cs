using System;
using System.Collections.Generic;
using System.Text;

namespace MatrixBillAcceptor.UsbHid
{
    internal class DataRecievedEventArgs : EventArgs
    {
        public readonly byte[] data;

        public DataRecievedEventArgs(byte[] data)
        {
            this.data = data;
        }
    }

    internal class DataSendEventArgs : EventArgs
    {
        public readonly byte[] data;

        public DataSendEventArgs(byte[] data)
        {
            this.data = data;
        }
    }

    internal delegate void DataRecievedEventHandler(object sender, DataRecievedEventArgs args);
    internal delegate void DataSendEventHandler(object sender, DataSendEventArgs args);

    internal class SpecifiedDevice : HidDevice
    {
        public event DataRecievedEventHandler DataRecieved;
        public event DataSendEventHandler DataSend;

        public override InputReport CreateInputReport()
        {
            return new SpecifiedInputReport(this);
        }

        public static SpecifiedDevice FindSpecifiedDevice(int vendor_id, int product_id)
        {
            return (SpecifiedDevice)FindDevice(vendor_id, product_id, typeof(SpecifiedDevice));
        }

        protected override void HandleDataReceived(InputReport oInRep)
        {
            if (DataRecieved != null)
            {
                SpecifiedInputReport report = (SpecifiedInputReport)oInRep;
                DataRecieved(this, new DataRecievedEventArgs(report.Data));
            }
        }

        public void SendData(byte[] data)
        {
            SpecifiedOutputReport oRep = new SpecifiedOutputReport(this);
            oRep.SendData(data);
            try
            {
                Write(oRep);
                if (DataSend != null)
                {
                    DataSend(this, new DataSendEventArgs(data));
                }
            }catch (HidDeviceException)
            {
                Console.WriteLine("Device didn't respond.");
            }catch (Exception ex)
            {
                Console.WriteLine(ex.ToString());
            }
        }
    }
}
