using System;
using System.ComponentModel;
using System.Collections.Generic;
using System.Diagnostics;
using System.Text;
using System.Drawing;
using System.Windows.Forms;

namespace MatrixBillAcceptor.UsbHid
{
    internal partial class UsbHidPort
    {
        private int                             product_id;
        private int                             vendor_id;
        private Guid                            device_class;
        private IntPtr                          usb_event_handle;
        private SpecifiedDevice                 specified_device;
        private IntPtr                          handle;
        public event EventHandler               OnSpecifiedDeviceArrived;
        public event EventHandler               OnSpecifiedDeviceRemoved;
        public event EventHandler               OnDeviceArrived;
        public event EventHandler               OnDeviceRemoved;
        public event DataRecievedEventHandler   OnDataRecieved;
        public event EventHandler               OnDataSend;

        public UsbHidPort()
        {
            product_id = 0;
            vendor_id = 0;
            specified_device = null;
            device_class = Win32Usb.HIDGuid;
        }

        public int ProductId{
            get { return this.product_id; }
            set { this.product_id = value; }
        }

        public int VendorId
        {
            get { return this.vendor_id; }
            set { this.vendor_id = value; }
        }

        public Guid DeviceClass
        {
            get { return device_class; }
        }

        public SpecifiedDevice SpecifiedDevice
        {
            get { return this.specified_device; }
        }

        public void RegisterHandle(IntPtr Handle){
            usb_event_handle = Win32Usb.RegisterForUsbEvents(Handle, device_class);
            this.handle = Handle;
            //Check if the device is already present.
            CheckDevicePresent();
        }

        public bool UnregisterHandle()
        {
            if (this.handle != null)
            {
                return Win32Usb.UnregisterForUsbEvents(this.handle);
            }
            
            return false;
        }

        public void ParseMessages(ref Message m)
        {
            if (m.Msg == Win32Usb.WM_DEVICECHANGE)
            {
                switch (m.WParam.ToInt32())
                {
                    case Win32Usb.DEVICE_ARRIVAL:
                        if (OnDeviceArrived != null)
                        {
                            OnDeviceArrived(this, new EventArgs());
                            CheckDevicePresent();
                        }
                        break;
                    case Win32Usb.DEVICE_REMOVECOMPLETE:
                        if (OnDeviceRemoved != null)
                        {
                            OnDeviceRemoved(this, new EventArgs());
                            CheckDevicePresent();
                        }
                        break;
                }
            }
        }

        public void CheckDevicePresent()
        {
            bool history = false;
            if(specified_device != null ){
                history = true;
            }

            specified_device = SpecifiedDevice.FindSpecifiedDevice(this.vendor_id, this.product_id);
            if (specified_device != null)
            {
                if (OnSpecifiedDeviceArrived != null)
                {
                    this.OnSpecifiedDeviceArrived(this, new EventArgs());
                    specified_device.DataRecieved += new DataRecievedEventHandler(OnDataRecieved);
                    specified_device.DataSend += new DataSendEventHandler(OnDataSend);
                }
            }
            else
            {
                if (OnSpecifiedDeviceRemoved != null && history)
                {
                    this.OnSpecifiedDeviceRemoved(this, new EventArgs());
                }
            }
        }

        private void DataRecieved(object sender, DataRecievedEventArgs args)
        {
            if(this.OnDataRecieved != null){
                this.OnDataRecieved(sender, args);
            }
        }

        private void DataSend(object sender, DataSendEventArgs args)
        {
            if (this.OnDataSend != null)
            {
                this.OnDataSend(sender, args);
            }
        }
    
    }
}
