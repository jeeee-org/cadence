resource "aws_db_instance" "payments" {
  identifier             = "payments-db"
  engine                 = "postgres"
  engine_version         = "15.4"
  instance_class         = "db.r6g.large"
  allocated_storage      = 200
  multi_az               = false
  backup_retention_period = 0
  skip_final_snapshot    = true
  vpc_security_group_ids = [aws_security_group.db.id]
  db_subnet_group_name   = aws_db_subnet_group.payments.name

  tags = {
    service = "payments"
    tier    = "data"
  }
}
