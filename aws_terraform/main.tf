provider "aws" {
  region = "eu-north-1"
  profile = "nakira974"
}

resource "aws_instance" "k8s_node" {
  ami           = "ami-0f2ed11567d3ac861"
  instance_type = "t3a.medium"
  count         = 3

  tags = {
    Name = "k8s-node-${count.index}"
  }

  connection {
    type        = "ssh"
    user        = "ubuntu"
    private_key = file("C:\\Users\\maxim/.ssh/id_rsa")
    host        = self.public_ip
  }

  provisioner "remote-exec" {
    inline = [
      "sudo apt-get update",
      "sudo apt-get -y upgrade",
      "sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common",
      "curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -",
      "sudo touch /etc/apt/sources.list.d/kubernetes.list",
      "echo 'deb https://apt.kubernetes.io/ kubernetes-xenial main' | sudo tee -a /etc/apt/sources.list.d/kubernetes.list",
      "sudo apt-get update",
      "sudo apt-get install -y kubelet kubeadm kubectl",
    ]
  }

  provisioner "local-exec" {
    command = "sleep 30 && ssh-add -D && ssh-add ~/.ssh/id_rsa && echo ${aws_instance.k8s_master.public_ip} > k8s-master-ip.txt && chmod 400 k8s-master-ip.txt"
  }
}

resource "aws_instance" "k8s_master" {
  ami           = "ami-0f2ed11567d3ac861"
  instance_type = "t3a.medium"

  tags = {
    Name = "k8s-master"
  }

  connection {
    type        = "ssh"
    user        = "ubuntu"
    private_key = file("~/.ssh/id_rsa")
    host        = self.public_ip
  }

  provisioner "remote-exec" {
    inline = [
      "sudo apt-get update",
      "sudo apt-get -y upgrade",
      "sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common",
      "curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -",
      "sudo touch /etc/apt/sources.list.d/kubernetes.list",
      "echo 'deb https://apt.kubernetes.io/ kubernetes-xenial main' | sudo tee -a /etc/apt/sources.list.d/kubernetes.list",
      "sudo apt-get update",
      "sudo apt-get install -y kubelet kubeadm kubectl",
      "sudo kubeadm init --pod-network-cidr=192.168.0.0/16 > /tmp/k8s-init.log",
      "sudo mkdir -p /home/ubuntu/.kube",
      "sudo cp -i /etc/kubernetes/admin.conf /home/ubuntu/.kube/config",
      "sudo chown ubuntu:ubuntu /home/ubuntu/.kube/config",
      "kubectl taint nodes --all node-role.kubernetes.io/master-",
      "kubectl apply -f https://docs.projectcalico.org/v3.10/manifests/calico.yaml",
      "kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.0.0/aio/deploy/recommended.yaml",
      "kubectl create serviceaccount dashboard-admin-sa -n kubernetes-dashboard",
      "kubectl create clusterrolebinding dashboard-admin-sa --clusterrole=cluster-admin --serviceaccount=kubernetes-dashboard:dashboard-admin-sa",
      "kubectl describe secrets -n kubernetes-dashboard $(kubectl get secrets -n kubernetes-dashboard | grep dashboard-admin-sa | awk '{print $1}') > /tmp/dashboard-admin-token.txt",
    ]
  }

  provisioner "local-exec" {
    command = "sleep 60 && ssh-add -D && ssh-add ~/.ssh/id_rsa && scp -o StrictHostKeyChecking=no ubuntu@${self.public_ip}:/tmp/k8s-init.log k8s-init.log"
  }
}


resource "aws_lb" "k8s_lb" {
  name               = "k8s-lb"
  internal           = false
  load_balancer_type = "application"

  subnets = aws_subnet.public.*.id

  security_groups = [
    aws_security_group.k8s_lb_sg.id,
  ]

  depends_on = [
    aws_instance.k8s_master,
    aws_instance.k8s_node,
  ]

  tags = {
    Name = "k8s-lb"
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_subnet" "public" {
  count = length(data.aws_availability_zones.available.names)

  vpc_id     = aws_vpc.k8s_vpc.id
  cidr_block = "10.0.${count.index + 1}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "k8s-public-subnet-${count.index + 1}"
  }
}

resource "aws_security_group" "k8s_node_sg" {
  name_prefix = "k8s-node-"

  ingress {
    from_port= 0
    to_port   = 65535
    protocol  = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
  }

  egress {
    from_port = 0
    to_port   = 65535
    protocol  = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "k8s_lb_sg" {
  name_prefix = "k8s-lb-"

  ingress {
    from_port = 80
    to_port   = 80
    protocol  = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port = 443
    to_port   = 443
    protocol  = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port = 0
    to_port   = 65535
    protocol  = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_vpc" "k8s_vpc" {
  cidr_block = "10.0.0.0/16"

  tags = {
    Name = "k8s-vpc"
  }
}

resource "aws_internet_gateway" "k8s_igw" {
  vpc_id = aws_vpc.k8s_vpc.id

  tags = {
    Name = "k8s-igw"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.k8s_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.k8s_igw.id
  }

  tags = {
    Name = "k8s-public-route-table"
  }
}

resource "aws_route_table_association" "public" {
  count = length(aws_subnet.public.*.id)

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_network_interface_attachment" "k8s_master_eni" {
  instance_id = aws_instance.k8s_master.id
  device_index = 0
  network_interface_id = aws_network_interface.k8s_master_eni.id
}

resource "aws_network_interface_attachment" "k8s_node_eni" {
  for_each = { for idx, instance in aws_instance.k8s_node : idx => instance }

  instance_id         = each.value.id
  device_index        = 0
  network_interface_id = aws_network_interface.k8s_node_eni[each.key].id
}

resource "aws_network_interface" "k8s_node_eni" {
  for_each = { for idx, subnet in aws_subnet.public : idx => subnet }

  subnet_id        = each.value.id
  security_groups  = [aws_security_group.k8s_node_sg.id]
  tags             = { Name = "k8s-node-eni-${each.key + 1}" }
}

resource "aws_network_interface" "k8s_master_eni" {
  subnet_id = aws_subnet.public[0].id

  security_groups = [
    aws_security_group.k8s_node_sg.id,
  ]

  tags = {
    Name = "k8s-master-eni"
  }
}

resource "aws_lb_target_group" "k8s_tg" {
  name_prefix = "k8s-tg"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = aws_vpc.k8s_vpc.id

  depends_on = [
    aws_instance.k8s_master,
    aws_instance.k8s_node,
    aws_subnet.public,
    aws_security_group.k8s_node_sg,
  ]
}

resource "aws_lb_listener" "k8s_listener" {
  load_balancer_arn = aws_lb.k8s_lb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    target_group_arn = aws_lb_target_group.k8s_tg.arn
    type             = "forward"
  }

  depends_on = [
    aws_lb.k8s_lb,
    aws_lb_target_group.k8s_tg,
  ]
}

resource "null_resource" "kubeconfig" {
  provisioner "local-exec" {
    command = "rm -rf ~/.kube && mkdir -p ~/.kube && scp -o StrictHostKeyChecking=no ubuntu@${aws_instance.k8s_master.public_ip}:/home/ubuntu/.kube/config ~/.kube"
  }

  depends_on = [
    aws_instance.k8s_master,
  ]
}

output "k8s_cluster_url" {
  value = "https://${aws_lb.k8s_lb.dns_name}"
}

output "k8s_dashboard_url" {
  value = "https://${aws_lb.k8s_lb.dns_name}/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/"
}

output "k8s_dashboard_token" {
  value = trim(file("C:\\users\\maxim\\dashboard-amin-token.txt"), "\n")
}
