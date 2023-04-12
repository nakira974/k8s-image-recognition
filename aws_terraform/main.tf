provider "aws" {
  region = "eu-north-1"
  profile = "nakira974"
}

resource "aws_vpc" "k8s_vpc" {
  cidr_block = "10.0.0.0/16"

  tags = {
    Name = "k8s-vpc"
  }
}

data "template_file" "master_data" {
  template = "${file("master_data.sh")}"
}

data "template_file" "node_data" {
  template = "${file("node_data.sh")}"
}

resource "aws_key_pair" "nakira974-ssh" {
  key_name   = "nakira974-ssh"
  public_key = file("~/.ssh/id_rsa.pub")
}

# New resource to allocate an Elastic IP for the NAT Gateway
resource "aws_eip" "nat" {
  vpc = true
}

# New resource to create the NAT Gateway in a public subnet
resource "aws_nat_gateway" "nat" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public[0].id
}

resource "aws_instance" "k8s_node" {
  ami           = "ami-064087b8d355e9051"
  instance_type = "t3.medium"
  associate_public_ip_address = true
  count         = 3
  key_name= "nakira974-ssh"
  tags = {
    Name = "k8s-node-${count.index}"
  }

  user_data = "${data.template_file.node_data.template}"
}



resource "aws_instance" "k8s_master" {
  ami           = "ami-064087b8d355e9051"
  associate_public_ip_address = true
  instance_type = "t3.medium"
  key_name= "nakira974-ssh"

  tags = {
    Name = "k8s-master"
  }

  user_data = "${data.template_file.master_data.template}"
}
# Add a NAT Gateway route to the Kubernetes nodes and master instances via the ENIs
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.k8s_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat.id
  }

  tags = {
    Name = "k8s-private-route-table"
  }
}

resource "aws_route_table_association" "private" {
  count = length(aws_subnet.public.*.id)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.private.id

  depends_on = [
    aws_nat_gateway.nat,
    aws_route_table.private,
  ]
}
data "aws_subnet" "public" {
  for_each = toset([for idx, _ in aws_subnet.public : aws_subnet.public[idx].id])

  id = each.key
}

resource "aws_network_interface" "k8s_node_eni" {
  for_each = { for idx, subnet in aws_subnet.public : idx => subnet }

  subnet_id = each.value.id
  security_groups = [aws_security_group.k8s_node_sg.id]

  tags = {
    Name = "k8s-node-eni-${each.key + 1}"
  }

  # Add a reference to the private route table with a route to the NAT Gateway
  depends_on = [
    aws_route_table_association.private,
  ]

  private_ip = "10.0.${each.key}.100"

  availability_zone = data.aws_subnet.public[each.value.id].availability_zone
}

resource "aws_network_interface" "k8s_master_eni" {
  subnet_id = aws_subnet.public[0].id
  security_groups = [
    aws_security_group.k8s_node_sg.id,
  ]

  tags = {
    Name = "k8s-master-eni"
  }

  # Add a reference to the private route table with a route to the NAT Gateway
  depends_on = [
    aws_route_table_association.private,
  ]

  private_ip = "10.0.0.100"
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
  cidr_block = "10.0.${count.index}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "k8s-public-subnet-${count.index + 1}"
  }
}

resource "aws_security_group" "k8s_node_sg" {
  name_prefix = "k8s-node-"
  vpc_id = aws_vpc.k8s_vpc.id
  ingress {
    from_port= 0
    to_port   = 65535
    protocol  = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 0
    to_port     = -1
    protocol    = "icmp"
    cidr_blocks = ["0.0.0.0/0"]
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
  vpc_id = aws_vpc.k8s_vpc.id
  ingress {
    from_port = 80
    to_port   = 80
    protocol  = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }


  ingress {
    from_port = 22
    to_port   = 22
    protocol  = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 0
    to_port     = -1
    protocol    = "icmp"
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



resource "aws_network_interface_attachment" "k8s_node_eni" {
  for_each = { for idx, instance in aws_instance.k8s_node : idx => instance }
  instance_id         = each.value.id
  device_index        = 1
  network_interface_id = aws_network_interface.k8s_node_eni[each.key].id
}

resource "aws_network_interface_attachment" "k8s_master_eni" {
  instance_id          = aws_instance.k8s_master.id
  device_index         = 1
  network_interface_id = aws_network_interface.k8s_master_eni.id
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


variable "enable_dashboard" {
  description = "Whether to enable Kubernetes dashboard access through the load balancer"
  type        = bool
  default     = true
}

resource "aws_lb_listener" "k8s_listener" {
  load_balancer_arn = aws_lb.k8s_lb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    target_group_arn = aws_lb_target_group.k8s_tg.arn
    type             = "forward"
  }
}
# Create an additional target group for the Kubernetes dashboard service
resource "aws_lb_target_group" "k8s_dashboard_tg" {
  name_prefix = "kda-tg"
  port        = 443
  protocol    = "HTTPS"
  vpc_id      = aws_vpc.k8s_vpc.id

  health_check {
    path = "/"

    matcher = "200-399"
  }

  depends_on = [
    aws_instance.k8s_master,
    aws_subnet.public,
    aws_security_group.k8s_node_sg,
  ]
}


output "k8s_cluster_url" {
  value = "https://${aws_lb.k8s_lb.dns_name}"
}

output "k8s_dashboard_url" {
  value = "https://${aws_lb.k8s_lb.dns_name}/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/"
}

output "k8s_dashboard_token" {
  value = trim(file("/tmp/dashboard-admin-token.txt"), "\n")
}

output "public_ips" {
  value = [
    aws_instance.k8s_master.public_ip,
    aws_instance.k8s_node.*.public_ip
  ]
}